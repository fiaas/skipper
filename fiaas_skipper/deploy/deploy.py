#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

from copy import copy
import collections
import logging
import time
import uuid
from threading import Thread, Lock

import yaml
from k8s.client import NotFound
from k8s.models.common import ObjectMeta
from k8s.models.deployment import Deployment
from prometheus_client import Counter, Gauge

LOG = logging.getLogger(__name__)
NAME = 'fiaas-deploy-daemon'
DEPLOY_INTERVAL = 30
STATUS_UPDATE_INTERVAL = 300
DEPLOYMENT_TRACKING_TIMEOUT = 300
DEPLOYMENT_TRACKING_INTERVAL = 10

last_deploy_gauge = Gauge("last_triggered_deployment", "Timestamp for when last deployment was performed")
deploy_counter = Counter("deployments_triggered", "Number of deployments triggered and performed")
fiaas_enabled_namespaces_gauge = Gauge("fiaas_enabled_namespaces", "Number of namespaces that are FIAAS enabled")

Status = collections.namedtuple('Status', ['summary', 'description'])


class DeploymentStatus(object):
    def __init__(self, name, namespace, status, description, version, channel=None):
        self.name = name
        self.namespace = namespace
        self.status = status
        self.description = description
        self.version = version
        self.channel = channel


class Deployer(object):
    def __init__(self, cluster, release_channel_factory, bootstrap, status, spec_config_extension=None,
                 deploy_interval=DEPLOY_INTERVAL):
        self._cluster = cluster
        self._release_channel_factory = release_channel_factory
        self._bootstrap = bootstrap
        self._spec_extension = spec_config_extension
        self._deploy_interval = deploy_interval
        self._status = status

    def deploy(self, namespaces=None):
        deploy_counter.inc()
        last_deploy_gauge.set_to_current_time()
        deployment_configs = self._cluster.find_deployment_configs(NAME)
        fiaas_enabled_namespaces_gauge.set(len(deployment_configs))
        for deployment_config in deployment_configs:
            if namespaces and deployment_config.namespace not in namespaces:
                continue
            try:
                channel = self._release_channel_factory(deployment_config.name, deployment_config.tag)
                spec_config = self._load_spec(channel)
                LOG.debug(spec_config)
                self._status.track_deployment(deployment_config.namespace, channel.metadata["image"])
                self._deploy(deployment_config, channel, spec_config)
                if requires_bootstrap(deployment_config):
                    self._bootstrap(deployment_config, channel, spec_config)
            except Exception:
                LOG.exception("Failed to deploy %s in %s", deployment_config.name, deployment_config.namespace)
            time.sleep(self._deploy_interval)

    def status(self):
        return self._status()

    def _deploy(self, deployment_config, channel, spec_config):
        raise NotImplementedError("Subclass must override _deploy")

    def _load_spec(self, channel):
        spec_config = yaml.safe_load(channel.spec)
        return self._merge_extensions(spec_config)

    def _merge_extensions(self, spec_config):
        """This naively overwrites the value of the given key if present
        We may choose to do some smart merging supporting nested dictionaries at a later
        point but for now this simple behavior is sufficient
        """
        if not self._spec_extension:
            return spec_config
        self._log_changes(spec_config)
        spec_config.update(self._spec_extension)
        return spec_config

    def _log_changes(self, spec_config):
        for key in self._spec_extension:
            if key in spec_config:
                LOG.debug("Overwriting spec: " + key +
                          "=" + str(self._spec_extension[key]) +
                          " originally: " + key + "=" + str(spec_config[key]))
            else:
                LOG.debug("Extending spec with key: " + key +
                          "=" + str(self._spec_extension[key]))

    @staticmethod
    def _create_metadata(deployment_config):
        labels = {
            "app": deployment_config.name,
            "heritage": "FIAAS-Skipper",
            "fiaas/bootstrap": "true",
            "fiaas/deployment_id": str(uuid.uuid4())
        }
        return ObjectMeta(name=deployment_config.name,
                          namespace=deployment_config.namespace,
                          labels=labels)

    def _application(self):
        raise NotImplementedError("Subclass must override _application")


def requires_bootstrap(deployment_config):
    try:
        Deployment.get(name=deployment_config.name, namespace=deployment_config.namespace)
        return False
    except NotFound:
        return True
    except Exception as e:
        LOG.warning(e, exc_info=True)


def _get_version(dep):
    return None if dep is None else dep.spec.template.spec.containers[0].image.split(":")[-1]


def _get_status(dep, app):
    if dep is None:
        return Status('NOT_FOUND', 'No deployment found')
    if app is None:
        return Status('VERSION_MISMATCH', 'Application is not defined')
    if not app or dep.spec.template.spec.containers[0].image != app.spec.image:
        return Status('VERSION_MISMATCH', 'Deployment does not match application version')
    try:
        if dep.status.availableReplicas < dep.spec.replicas:
            return Status('FAILED', 'Available replicas does not match the number of replicas in spec')
        # TODO the k8s deployment model can be extended to include ready replicas and status
    except TypeError:
        return Status('UNAVAILABLE', 'Unable to determine available/ready replicas from k8s server')
    return Status('OK', '')


statuslock = Lock()


class StatusTracker(Thread):
    def __init__(self, cluster):
        Thread.__init__(self)
        self._cluster = cluster
        self._status = {}
        self._deployments = {}

    def __call__(self):
        def _deploying(status):
            if status.namespace in self._deployments.keys():
                status.status = 'DEPLOYING'
                status.description = 'Deploying version %s' % self._deployments[status.namespace]
            return status
        with statuslock:
            return tuple([_deploying(copy(status)) for status in self._status.values()])

    def _application(self):
        raise NotImplementedError("Subclass must override _application")

    def _get_status(self, namespace=None):
        deployment_configs = self._cluster.find_deployment_configs(NAME, namespace=namespace)
        deployments = {d.metadata.namespace: d for d in Deployment.find(NAME, namespace=namespace)}
        applications = {d.metadata.namespace: d for d in self._application().find(NAME, namespace=namespace)}
        res = []
        for c in deployment_configs:
            dep = deployments.get(c.namespace)
            app = applications.get(c.namespace)
            version = _get_version(dep)
            status = _get_status(dep, app)
            res.append(DeploymentStatus(name=NAME,
                                        namespace=c.namespace,
                                        status=status.summary,
                                        description=status.description,
                                        version=version or '',
                                        channel=c.tag or ''))
        return res

    def track_deployment(self, namespace, version):
        t = Thread(target=self._track_deployment, args=(namespace, version),
                   name="track_deployment_{}_{}".format(namespace, version.split(':')[1]), daemon=True)
        t.start()

    def _set_deployment_flag(self, namespace, version):
        with statuslock:
            self._deployments[namespace] = version

    def _unset_deployment_flag(self, namespace):
        with statuslock:
            del self._deployments[namespace]

    def _track_deployment(self, namespace, version):
        self._set_deployment_flag(namespace, version)
        timeout = time.time() + DEPLOYMENT_TRACKING_TIMEOUT
        time.sleep(10)  # Delay to allow termination to start
        while True:
            status = self._get_status(namespace=namespace)[0]
            if status and status.status == 'OK':
                with statuslock:
                    self._status[namespace] = status
                break
            if time.time() > timeout:
                break
            time.sleep(DEPLOYMENT_TRACKING_INTERVAL)
        self._unset_deployment_flag(namespace)

    def _update_status(self):
        with statuslock:
            self._status = {status.namespace: status for status in self._get_status()}

    def run(self):
        while True:
            self._update_status()
            time.sleep(STATUS_UPDATE_INTERVAL)
