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
