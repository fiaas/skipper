#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import json

import pytest
from flask import Flask
from mock import mock

from fiaas_skipper.deploy.deploy import Deployer, DeploymentStatus, StatusTracker
from fiaas_skipper.web.api import api


class TestApi(object):
    @pytest.fixture
    def deployer(self):
        return mock.create_autospec(Deployer)

    @pytest.fixture
    def status(self):
        return mock.create_autospec(StatusTracker, instance=True)

    @pytest.fixture
    def app(self, deployer, status):
        app = Flask(__name__)
        api.deployer = deployer
        api.status = status
        app.register_blueprint(api)
        return app.test_client()

    def test_empty_status(self, app, status):
        status.return_value = []
        response = app.get('/api/status')
        assert response.status_code == 200
        assert json.loads(response.data) == []

    def test_status(self, app, status):
        status.return_value = [
            DeploymentStatus(name='fiaas-deploy-daemon',
                             namespace='default',
                             status='OK',
                             description='All good',
                             version="fiaas/fiaas-deploy-daemon:123",
                             channel="stable")]
        response = app.get('/api/status')
        assert response.status_code == 200
        assert json.loads(response.data) == [{
            "status": "OK",
            "namespace": "default",
            "name": "fiaas-deploy-daemon",
            "description": "All good",
            "version": "fiaas/fiaas-deploy-daemon:123",
            "channel": "stable"
        }]

    def test_deploy(self, app, deployer):
        response = app.post('/api/deploy')
        assert response.status_code == 200
        deployer.deploy.assert_called_with(force_bootstrap=False, namespaces=None)

    def test_deploy_force_bootstrap(self, app, deployer):
        response = app.post('/api/deploy', json={'force_bootstrap': True, 'namespaces': ['test1']})
        assert response.status_code == 200
        deployer.deploy.assert_called_with(force_bootstrap=True, namespaces=['test1'])
