#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import pytest
from flask import Flask

from fiaas_skipper.web.metrics import metrics


class TestMetrics(object):
    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.register_blueprint(metrics)
        return app.test_client()

    def test_metrics(self, app):
        response = app.get('/_/metrics')
        assert response.status_code == 200
