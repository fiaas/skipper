#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging
import uuid

from k8s.client import NotFound
from k8s.models.common import ObjectMeta
from k8s.models.configmap import ConfigMap
from k8s.models.deployment import Deployment

LOG = logging.getLogger(__name__)
NAME = 'fiaas-deploy-daemon'


class Deployer(object):
    def __init__(self, cluster, release_channel_factory, bootstrap, ingress_suffix):
        self._cluster = cluster
        self._release_channel_factory = release_channel_factory
        self._bootstrap = bootstrap
        self._ingress_suffix = ingress_suffix

    def deploy(self):
        deployment_configs = self._cluster.find_deployment_configs(NAME)
        for deployment_config in deployment_configs:
            channel = self._release_channel_factory(deployment_config.name, deployment_config.tag)
            self._deploy(deployment_config, channel)
            if requires_bootstrap(deployment_config):
                self._bootstrap(deployment_config, channel)

    def _deploy(self):
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


def requires_bootstrap(deployment_config):
    try:
        Deployment.get(name=deployment_config.name, namespace=deployment_config.namespace)
        return False
    except NotFound:
        return True
    except Exception as e:
        LOG.warn(e, exc_info=True)


def generate_config(template, namespace, ingress_suffix):
    config = dict(template)
    config['host'] = "".join([NAME, '-', namespace, '.', ingress_suffix])
    return config
