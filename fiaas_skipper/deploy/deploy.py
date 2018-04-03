#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging
import uuid

import pkg_resources
import yaml
from k8s.client import NotFound
from k8s.models.common import ObjectMeta
from k8s.models.configmap import ConfigMap
from k8s.models.deployment import Deployment
from prometheus_client import Counter, Gauge

LOG = logging.getLogger(__name__)
NAME = 'fiaas-deploy-daemon'

last_deploy_gauge = Gauge("last_triggered_deployment", "Timestamp for when last deployment was performed")
deploy_counter = Counter("deployments_triggered", "Number of deployments triggered and performed")
fiaas_enabled_namespaces_gauge = Gauge("fiaas_enabled_namespaces", "Number of namespaces that are FIAAS enabled")


class Deployer(object):
    def __init__(self, cluster, release_channel_factory, bootstrap):
        self._cluster = cluster
        self._release_channel_factory = release_channel_factory
        self._bootstrap = bootstrap

    def deploy(self):
        deploy_counter.inc()
        last_deploy_gauge.set_to_current_time()
        deployment_configs = self._cluster.find_deployment_configs(NAME)
        fiaas_enabled_namespaces_gauge.set(len(deployment_configs))
        for deployment_config in deployment_configs:
            channel = self._release_channel_factory(deployment_config.name, deployment_config.tag)
            self._deploy(deployment_config, channel)
            if requires_bootstrap(deployment_config):
                self._bootstrap(deployment_config, channel)

    def _deploy(self, deployment_config, channel):
        raise NotImplementedError("Subclass must override _deploy")

    @staticmethod
    def _create_metadata(deployment_config):
        return ObjectMeta(name=deployment_config.name,
                          namespace=deployment_config.namespace,
                          labels={"fiaas/bootstrap": "true", "fiaas/deployment_id": str(uuid.uuid4())})


class DeploymentConfig(object):
    def __init__(self, name, namespace, tag):
        self.name = name
        self.namespace = namespace
        self.tag = tag


class DeploymentConfigStatus(object):
    def __init__(self, name, namespace, status, description):
        self.name = name
        self.namespace = namespace
        self.status = status
        self.description = description


class Cluster(object):
    @staticmethod
    def find_deployment_configs(name):
        res = []
        configmaps = [c for c in ConfigMap.list(namespace=None) if c.metadata.name == name]
        for c in configmaps:
            tag = c.data['tag'] if 'tag' in c.data else 'stable'
            res.append(DeploymentConfig(name=NAME, namespace=c.metadata.namespace, tag=tag))
        return res

    @staticmethod
    def find_deployment_config_statuses(name):
        res = []
        configmaps = [c for c in ConfigMap.list(namespace=None) if c.metadata.name == name]
        for c in configmaps:
            description = None
            try:
                dep = Deployment.get(name=name, namespace=c.metadata.namespace)
                if dep.status.availableReplicas >= dep.spec.replicas:
                    status = 'SUCCESS'
                else:
                    status = 'FAILED'
                    description = 'Available replicas does not match the number of replicas in spec'
            except NotFound:
                status = 'NOT FOUND'
                description = 'No deployment found for given namespace - needs bootstrapping'
            except Exception as e:
                LOG.warn(e, exc_info=True)
                status = 'ERROR'
                description = e.message
            res.append(DeploymentConfigStatus(name=name,
                                              namespace=c.metadata.namespace,
                                              status=status,
                                              description=description))
        return res


def requires_bootstrap(deployment_config):
    try:
        Deployment.get(name=deployment_config.name, namespace=deployment_config.namespace)
        return False
    except NotFound:
        return True
    except Exception as e:
        LOG.warning(e, exc_info=True)


_resource_stream = pkg_resources.resource_stream(__name__, "fiaas.yml")
default_config_template = yaml.safe_load(_resource_stream)
