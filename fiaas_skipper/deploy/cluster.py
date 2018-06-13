#!/usr/bin/env python
# -*- coding: utf-8

import logging

from k8s.client import NotFound
from k8s.models.configmap import ConfigMap
from k8s.models.deployment import Deployment

LOG = logging.getLogger(__name__)


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
        configmaps = ConfigMap.find(name, namespace=None)
        for c in configmaps:
            tag = c.data['tag'] if 'tag' in c.data else 'stable'
            res.append(DeploymentConfig(name=name, namespace=c.metadata.namespace, tag=tag))
        return res

    @staticmethod
    def find_deployment_config_statuses(name):
        res = []
        configmaps = ConfigMap.find(name, namespace=None)
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
            except TypeError:
                status = 'UNAVAILABLE'
                pass
            except Exception as e:
                LOG.warn(e, exc_info=True)
                status = 'ERROR'
                description = e.message
            res.append(DeploymentConfigStatus(name=name,
                                              namespace=c.metadata.namespace,
                                              status=status,
                                              description=description))
        return res
