#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import pytest
from flask import Flask

from fiaas_skipper.web.healthcheck import healthcheck


class TestHealthcheck(object):
    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.register_blueprint(healthcheck)
        return app.test_client()

    def test_healthz(self, app):
        response = app.get('/healthz')
        assert response.status_code == 200
