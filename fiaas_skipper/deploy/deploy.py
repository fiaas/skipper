#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

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
    def __init__(self, cluster, release_channel_factory, bootstrap, spec_config_extension=None,
                 deploy_interval=DEPLOY_INTERVAL):
        self._cluster = cluster
        self._release_channel_factory = release_channel_factory
        self._bootstrap = bootstrap
        self._spec_extension = spec_config_extension
        self._deploy_interval = deploy_interval

    def deploy(self, namespaces=None, force_bootstrap=False):
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
                self._deploy(deployment_config, channel, spec_config)
                if force_bootstrap or requires_bootstrap(deployment_config):
                    self._bootstrap(deployment_config, channel, spec_config)
            except Exception:
                LOG.exception("Failed to deploy %s in %s", deployment_config.name, deployment_config.namespace)
            time.sleep(self._deploy_interval)

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


class StatusTracker(Thread):
    def __init__(self, cluster, application, interval):
        Thread.__init__(self)
        self.daemon = True
        self._cluster = cluster
        self._status = {}
        self._application = application
        self._statuslock = Lock()
        self._interval = interval

    def __call__(self):
        with self._statuslock:
            return tuple(self._status.values())

    def _get_status(self, namespace=None):
        deployment_configs = self._cluster.find_deployment_configs(NAME, namespace=namespace)
        deployments = {d.metadata.namespace: d for d in Deployment.find(NAME, namespace=namespace)}
        applications = {d.metadata.namespace: d for d in self._application.find(NAME, namespace=namespace)}
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

    def _update_status(self):
        new_status = self._get_status()
        with self._statuslock:
            self._status = {status.namespace: status for status in new_status}

    def run(self):
        while True:
            self._update_status()
            time.sleep(self._interval)
