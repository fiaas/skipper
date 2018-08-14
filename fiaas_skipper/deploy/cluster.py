#!/usr/bin/env python
# -*- coding: utf-8
import logging

from k8s.models.configmap import ConfigMap

LOG = logging.getLogger(__name__)


class DeploymentConfig(object):
    def __init__(self, name, namespace, tag):
        self.name = name
        self.namespace = namespace
        self.tag = tag


class Cluster(object):
    @staticmethod
    def find_deployment_configs(name):
        res = []
        configmaps = ConfigMap.find(name, namespace=None)
        for c in configmaps:
            tag = c.data['tag'] if 'tag' in c.data else 'stable'
            res.append(DeploymentConfig(name=name, namespace=c.metadata.namespace, tag=tag))
        return res
