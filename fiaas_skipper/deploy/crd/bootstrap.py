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

from ...deploy.bootstrap import BarePodBootstrapper
from .crd_resources_syncer_apiextensionsv1 import CrdResourcesSyncerApiextensionsV1
from .crd_resources_syncer_apiextensionsv1beta1 import CrdResourcesSyncerApiextensionsV1Beta1

LOG = logging.getLogger(__name__)


class CrdBootstrapper(BarePodBootstrapper):
    def __init__(self, use_apiextensionsv1_crd):
        cmd_args = ["--enable-crd-support"]
        if use_apiextensionsv1_crd:
            CrdResourcesSyncerApiextensionsV1.update_crd_resources()
            cmd_args.append("--use-apiextensionsv1-crd")
        else:
            CrdResourcesSyncerApiextensionsV1Beta1.update_crd_resources()
        super(CrdBootstrapper, self).__init__(cmd_args=cmd_args)
