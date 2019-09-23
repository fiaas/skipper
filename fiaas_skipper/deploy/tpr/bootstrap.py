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

from k8s.models.common import ObjectMeta
from k8s.models.third_party_resource import ThirdPartyResource, APIVersion

from ...deploy.bootstrap import BarePodBootstrapper

LOG = logging.getLogger(__name__)


class TprBootstrapper(BarePodBootstrapper):
    def __init__(self):
        def bootstrap():
            metadata = ObjectMeta(name="paasbeta-application.schibsted.io")
            paasbeta_application_resource = ThirdPartyResource.get_or_create(
                metadata=metadata, description='A paas application definition', versions=[APIVersion(name='v1beta')])
            paasbeta_application_resource.save()
            LOG.info("Created ThirdPartyResource with name PaasbetaApplication")
            metadata = ObjectMeta(name="paasbeta-status.schibsted.io")
            paasbeta_status_resource = ThirdPartyResource.get_or_create(
                metadata=metadata, description='A paas application status', versions=[APIVersion(name='v1beta')])
            paasbeta_status_resource.save()
            LOG.info("Created ThirdPartyResource with name PaasbetaStatus")
        bootstrap()
        super(TprBootstrapper, self).__init__(cmd_args=["--enable-tpr-support"])
