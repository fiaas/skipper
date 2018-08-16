#!/usr/bin/env python
# -*- coding: utf-8
import collections
import logging

from k8s.models.configmap import ConfigMap

LOG = logging.getLogger(__name__)

DeploymentConfig = collections.namedtuple('DeploymentConfig', ['name', 'namespace', 'tag'])


class Cluster(object):
    @staticmethod
    def find_deployment_configs(name, namespace=None):
        res = []
        configmaps = ConfigMap.find(name, namespace)
        for c in configmaps:
            tag = c.data['tag'] if 'tag' in c.data else 'stable'
            res.append(DeploymentConfig(name=name, namespace=c.metadata.namespace, tag=tag))
        return res
