#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging
import time
import uuid

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


class Deployer(object):
    def __init__(self, cluster, release_channel_factory, bootstrap, spec_config_extension=None, deploy_interval=DEPLOY_INTERVAL):
        self._cluster = cluster
        self._release_channel_factory = release_channel_factory
        self._bootstrap = bootstrap
        self._spec_extension = spec_config_extension
        self._deploy_interval = deploy_interval

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
                self._deploy(deployment_config, channel, spec_config)
                if requires_bootstrap(deployment_config):
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
