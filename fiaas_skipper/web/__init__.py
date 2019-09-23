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

from flask import Flask, request_started, request_finished, got_request_exception
from prometheus_client import Counter, Histogram

request_histogram = Histogram("web_request_latency", "Request latency in seconds", ["page"])

SELF = "'self'"
NONE = "'none'"


def _connect_signals():
    rs_counter = Counter("web_request_started", "HTTP requests received")
    request_started.connect(lambda s, *a, **e: rs_counter.inc(), weak=False)
    rf_counter = Counter("web_request_finished", "HTTP requests successfully handled")
    request_finished.connect(lambda s, *a, **e: rf_counter.inc(), weak=False)
    re_counter = Counter("web_request_exception", "Failed HTTP requests")
    got_request_exception.connect(lambda s, *a, **e: re_counter.inc(), weak=False)


def create_webapp(deployer, cluster, release_channel_factory, status):
    from flask_bootstrap import Bootstrap
    from flask_talisman import Talisman, DENY
    from ..web.api import api
    from ..web.frontend import frontend
    from ..web.healthcheck import healthcheck
    from ..web.metrics import metrics
    from .nav import nav
    app = Flask(__name__)
    # TODO: These options are like this because we haven't set up TLS
    csp = {'default-src': SELF, 'script-src': [SELF], 'style-src': [SELF], 'object-src': [NONE]}
    Talisman(app, frame_options=DENY, force_https=False, strict_transport_security=False,
             content_security_policy=csp)
    Bootstrap(app)
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    api.cluster = cluster
    api.deployer = deployer
    api.status = status
    frontend.release_channel_factory = release_channel_factory
    healthcheck.status = status
    app.register_blueprint(api)
    app.register_blueprint(frontend)
    app.register_blueprint(metrics)
    app.register_blueprint(healthcheck)
    nav.init_app(app)
    _connect_signals()
    return app
