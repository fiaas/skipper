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

import mock
import pytest
import yaml

from fiaas_skipper import CrdDeployer
from fiaas_skipper.deploy.channel import ReleaseChannel
from fiaas_skipper.deploy.cluster import DeploymentConfig
from fiaas_skipper.deploy.crd.types import FiaasApplicationSpec


class TestCrdDeployer(object):
    @pytest.fixture
    def cluster(self):
        cluster = mock.NonCallableMagicMock(name="cluster")
        cluster.find_deployment_configs.return_value = (
            DeploymentConfig("testapp", "test1", "stable", False),
        )
        return cluster

    @pytest.fixture
    def release_channel_factory(self):
        release_channel_factory = mock.MagicMock(name="release_channel_factory")
        release_channel_factory.return_value = ReleaseChannel(name="xx",
                                                              tag="stable",
                                                              metadata={"image": "image1",
                                                                        "spec": "http://example.com"},
                                                              spec=yaml.dump({"z": "z", "y": "1"}))
        return release_channel_factory

    @mock.patch('fiaas_skipper.deploy.crd.types.FiaasApplication.get_or_create', autospec=True)
    def test_deploy_creates_fiaas_application(self, get_or_create, cluster, release_channel_factory):
        app = mock.MagicMock()
        spec = mock.PropertyMock()
        type(app).spec = spec
        get_or_create.return_value = app
        bootstrap = mock.MagicMock()
        spec_config_ext = {"x": "x", "y": "66"}
        deployer = CrdDeployer(cluster, release_channel_factory, bootstrap, spec_config_extension=spec_config_ext,
                               deploy_interval=0)
        deployer.deploy()
        spec.assert_called_once_with(
            FiaasApplicationSpec(application="testapp", image="image1",
                                 config={"x": "x", "z": "z", "y": "66"}))
        app.save.assert_called_once()
