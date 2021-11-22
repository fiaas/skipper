#!/usr/bin/env python
# -*- coding: utf-8

# Copyright 2017-2019 The FIAAS Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import collections
import logging

from k8s.models.configmap import ConfigMap

LOG = logging.getLogger(__name__)

DeploymentConfig = collections.namedtuple(
    'DeploymentConfig', ['name', 'namespace', 'tag', 'service_account_per_app'])


class Cluster(object):
    @staticmethod
    def find_deployment_configs(name, namespace=None):
        res = []
        configmaps = ConfigMap.find(name, namespace)
        for c in configmaps:
            tag = 'stable'
            sa_per_app = False
            for k, v in c.data.items():
                if k == 'tag':
                    tag = v
                elif k == 'enable-service-account-per-app':
                    sa_per_app = v
            res.append(DeploymentConfig(
                name=name,
                namespace=c.metadata.namespace,
                tag=tag,
                service_account_per_app=sa_per_app,
            ))
        return res
