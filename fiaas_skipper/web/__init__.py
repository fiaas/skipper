#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

from flask import Flask, request_started, request_finished, got_request_exception
from prometheus_client import Counter, Histogram

from .platform_collector import PLATFORM_COLLECTOR

PLATFORM_COLLECTOR.collect()

request_histogram = Histogram("web_request_latency", "Request latency in seconds", ["page"])

SELF = "'self'"
UNSAFE_INLINE = "'unsafe-inline'"


def _connect_signals():
    rs_counter = Counter("web_request_started", "HTTP requests received")
    request_started.connect(lambda s, *a, **e: rs_counter.inc(), weak=False)
    rf_counter = Counter("web_request_finished", "HTTP requests successfully handled")
    request_finished.connect(lambda s, *a, **e: rf_counter.inc(), weak=False)
    re_counter = Counter("web_request_exception", "Failed HTTP requests")
    got_request_exception.connect(lambda s, *a, **e: re_counter.inc(), weak=False)


def create_webapp(deployer, cluster):
    from flask_bootstrap import Bootstrap
    from flask_talisman import Talisman, DENY
    from ..web.api import api
    from ..web.frontend import frontend
    from ..web.healthcheck import healthcheck
    from ..web.metrics import metrics
    from .nav import nav
    app = Flask(__name__)
    # TODO: These options are like this because we haven't set up TLS
    csp = {'default-src': SELF, 'script-src': [SELF, UNSAFE_INLINE], 'style-src': [SELF, UNSAFE_INLINE]}
    Talisman(app, frame_options=DENY, force_https=False, strict_transport_security=False,
             content_security_policy=csp)
    Bootstrap(app)
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    api.cluster = cluster
    api.deployer = deployer
    app.register_blueprint(api)
    app.register_blueprint(frontend)
    app.register_blueprint(metrics)
    app.register_blueprint(healthcheck)
    nav.init_app(app)
    _connect_signals()
    return app
