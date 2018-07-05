#!/usr/bin/env python
# -*- coding: utf-8

import logging

from k8s.models.configmap import ConfigMap
from k8s.models.deployment import Deployment

LOG = logging.getLogger(__name__)


class DeploymentConfig(object):
    def __init__(self, name, namespace, tag):
        self.name = name
        self.namespace = namespace
        self.tag = tag


class DeploymentConfigStatus(object):
    def __init__(self, name, namespace, status, description, version):
        self.name = name
        self.namespace = namespace
        self.status = status
        self.description = description
        self.version = version


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
        try:
            configmaps = ConfigMap.find(name, namespace=None)
            deployments = {d.metadata.namespace: d for d in Deployment.find(name, namespace=None)}
        except Exception:
            LOG.exception("Unable to get configmaps or deployments from k8s")
            return []
        res = []
        for c in configmaps:
            description = None
            version = None
            try:
                dep = deployments.get(c.metadata.namespace)
                if dep is None:
                    status = 'NOT FOUND'
                    description = 'No deployment found for given namespace - needs bootstrapping'
                else:
                    version = _get_version(dep)
                    if dep.status.availableReplicas >= dep.spec.replicas:
                        status = 'SUCCESS'
                    else:
                        status = 'FAILED'
                        description = 'Available replicas does not match the number of replicas in spec'
            except TypeError:
                status = 'UNAVAILABLE'
                description = 'Unable to read number of available replicas from k8s server'
            res.append(DeploymentConfigStatus(name=name,
                                              namespace=c.metadata.namespace,
                                              status=status,
                                              description=description,
                                              version=version))
        return res


def _get_version(dep):
    return dep.spec.template.spec.containers[0].image.split(":")[-1]
