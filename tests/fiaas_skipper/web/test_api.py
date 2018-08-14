#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import json

import pytest
from flask import Flask
from mock import patch, Mock, mock

from fiaas_skipper.deploy.deploy import Deployer, DeploymentStatus
from fiaas_skipper.web.api import api


class TestApi(object):
    @pytest.fixture
    def deployer(self):
        release_channel_factory = Mock()
        cluster = Mock()
        bootstrap = Mock()
        return Deployer(cluster=cluster,
                        release_channel_factory=release_channel_factory,
                        bootstrap=bootstrap,
                        deploy_interval=0)

    @pytest.fixture
    def app(self, deployer):
        app = Flask(__name__)
        api.deployer = deployer
        app.register_blueprint(api)
        return app.test_client()

    @pytest.fixture
    def deployment_status(self):
        with mock.patch("fiaas_skipper.deploy.deploy.Deployer.status") as status:
            yield status

    def test_empty_status(self, app, deployment_status):
        deployment_status.return_value = []
        response = app.get('/api/status')
        assert response.status_code == 200
        assert json.loads(response.data) == []

    def test_status(self, app, deployment_status):
        deployment_status.return_value = [
            DeploymentStatus(name='fiaas-deploy-daemon',
                             namespace='default',
                             status='OK',
                             description='All good',
                             version="fiaas/fiaas-deploy-daemon:123")]
        response = app.get('/api/status')
        assert response.status_code == 200
        assert json.loads(response.data) == [{
            "status": "OK",
            "namespace": "default",
            "name": "fiaas-deploy-daemon",
            "description": "All good",
            "version": "fiaas/fiaas-deploy-daemon:123"
        }]

    def test_deploy(self, app):
        with patch('fiaas_skipper.deploy.deploy.Deployer.deploy') as mock:
            response = app.post('/api/deploy')
            assert response.status_code == 200
            assert mock.called
