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

from __future__ import absolute_import

import logging

from .types import PaasbetaApplication, PaasbetaApplicationSpec
from ..deploy import Deployer

LOG = logging.getLogger(__name__)


class TprDeployer(Deployer):
    def _deploy(self, deployment_config, channel, spec_config):
        LOG.info("Deploying %s to %s", deployment_config.name, deployment_config.namespace)
        pba = PaasbetaApplication.get_or_create(metadata=self._create_metadata(deployment_config))
        pba.spec = self._create_paasbetaapplicationspec(name=deployment_config.name,
                                                        image=channel.metadata['image'],
                                                        spec_config=spec_config)
        pba.save()

    def _create_paasbetaapplicationspec(self, name, image, spec_config):
        return PaasbetaApplicationSpec(application=name, image=image, config=spec_config)
