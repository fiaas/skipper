#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import pytest
import mock
from threading import Thread
from flask import Flask

from fiaas_skipper.web.healthcheck import healthcheck


class TestHealthcheck(object):
    @pytest.fixture
    def app(self, request):
        app = Flask(__name__)
        healthcheck.status = mock.create_autospec(Thread)
        healthcheck.status.is_alive.return_value = request.param
        app.register_blueprint(healthcheck)
        return app.test_client()

    @pytest.mark.parametrize("app, status_code", [
        (False, 500),
        (True, 200),
    ], indirect=["app"])
    def test_healthz(self, app, status_code):
        response = app.get('/healthz')
        assert response.status_code == status_code
