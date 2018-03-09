#!/usr/bin/env python
# -*- coding: utf-8
import logging

from k8s.client import NotFound
from k8s.models.common import ObjectMeta
from k8s.models.configmap import ConfigMap
from k8s.models.deployment import Deployment

from fiaas_skipper.deploy.bootstrap import bootstrap, requires_bootstrap

LOG = logging.getLogger(__name__)
NAME = 'fiaas-deploy-daemon'


class Deployer(object):
    def __init__(self, cluster, release_channel_factory):
        self._cluster = cluster
        self._release_channel_factory = release_channel_factory

    def deploy(self):
        deployment_configs = self._cluster.find_deployment_configs(NAME)
        for deployment_config in deployment_configs:
            channel = self._release_channel_factory(deployment_config.name, deployment_config.tag)
            self._deploy(deployment_config, channel)
            if requires_bootstrap(deployment_config):
                bootstrap(deployment_config, channel)

    def _deploy(self):
        raise NotImplementedError("Subclass must override _deploy")

    @staticmethod
    def _create_metadata(deployment_config):
        return ObjectMeta(name=deployment_config.name,
                          namespace=deployment_config.namespace,
                          labels={"fiaas/bootstrap": "true"})


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
        configmaps = [c for c in ConfigMap.list() if c.metadata.name == name]
        for c in configmaps:
            tag = c.data['tag'] if 'tag' in c.data else 'stable'
            res.append(DeploymentConfig(name=NAME, namespace=c.metadata.namespace, tag=tag))
        return res

    @staticmethod
    def find_deployment_config_statuses(name):
        res = []
        configmaps = [c for c in ConfigMap.list() if c.metadata.name == name]
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
