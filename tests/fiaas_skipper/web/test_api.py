#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import json

import pytest
from flask import Flask
from mock import patch, Mock, create_autospec

from fiaas_skipper.deploy.cluster import DeploymentConfigStatus, Cluster
from fiaas_skipper.deploy.deploy import Deployer
from fiaas_skipper.web.api import api


class TestApi(object):
    @pytest.fixture
    def deployer(self, cluster):
        release_channel_factory = Mock()
        bootstrap = Mock()
        return Deployer(cluster=cluster,
                        release_channel_factory=release_channel_factory,
                        bootstrap=bootstrap)

    @pytest.fixture
    def cluster(self):
        return create_autospec(Cluster(), spec_set=True, instance=True)

    @pytest.fixture
    def app(self, cluster, deployer):
        app = Flask(__name__)
        api.cluster = cluster
        api.deployer = deployer
        app.register_blueprint(api)
        return app.test_client()

    def test_empty_status(self, app, cluster):
        cluster.find_deployment_config_statuses.return_value = []
        response = app.get('/api/status')
        cluster.find_deployment_config_statuses.assert_called_once_with('fiaas-deploy-daemon')
        assert response.status_code == 200
        assert json.loads(response.data) == []

    def test_status(self, app, cluster):
        cluster.find_deployment_config_statuses.return_value = [DeploymentConfigStatus(name='fiaas-deploy-daemon',
                                                                                       namespace='default',
                                                                                       status='OK',
                                                                                       description='All good')]
        response = app.get('/api/status')
        cluster.find_deployment_config_statuses.assert_called_once_with('fiaas-deploy-daemon')
        assert response.status_code == 200
        assert json.loads(response.data) == [
            {"status": "OK", "namespace": "default", "name": "fiaas-deploy-daemon", "description": "All good"}
        ]

    def test_deploy(self, app):
        with patch('fiaas_skipper.deploy.deploy.Deployer.deploy') as mock:
            response = app.post('/api/deploy')
            assert response.status_code == 200
            assert mock.called
