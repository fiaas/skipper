#!/usr/bin/env python
# -*- coding: utf-8
import json

import pinject
from flask import Flask, Blueprint, make_response, request_started, request_finished, got_request_exception
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram

from .platform_collector import PLATFORM_COLLECTOR
from ..deploy.deploy import DeploymentConfigStatus

PLATFORM_COLLECTOR.collect()

web = Blueprint("web", __name__)

request_histogram = Histogram("web_request_latency", "Request latency in seconds", ["page"])
status_histogram = request_histogram.labels("status")
metrics_histogram = request_histogram.labels("metrics")
deploy_histogram = request_histogram.labels("deploy")


@web.route("/_/metrics")
@metrics_histogram.time()
def metrics():
    resp = make_response(generate_latest())
    resp.mimetype = CONTENT_TYPE_LATEST
    return resp


@web.route('/')
def hello_world():
    return 'Hello World!'


@web.route('/status')
@status_histogram.time()
def status():
    deployment_config_statuses = web.cluster.find_deployment_config_statuses('fiaas-deploy-daemon')
    return make_response(json.dumps(deployment_config_statuses, default=_encode), 200)


def _encode(obj):
    if isinstance(obj, DeploymentConfigStatus):
        return obj.__dict__
    return obj


@web.route('/healthz')
def healthcheck():
    return make_response('', 200)


@web.route('/deploy', methods=['POST'])
@deploy_histogram.time()
def deploy():
    web.deployer.deploy()
    return make_response('', 200)


def _connect_signals():
    rs_counter = Counter("web_request_started", "HTTP requests received")
    request_started.connect(lambda s, *a, **e: rs_counter.inc(), weak=False)
    rf_counter = Counter("web_request_finished", "HTTP requests successfully handled")
    request_finished.connect(lambda s, *a, **e: rf_counter.inc(), weak=False)
    re_counter = Counter("web_request_exception", "Failed HTTP requests")
    got_request_exception.connect(lambda s, *a, **e: re_counter.inc(), weak=False)


class WebBindings(pinject.BindingSpec):
    def provide_webapp(self, deployer, cluster):
        app = Flask(__name__)
        app.register_blueprint(web)
        web.cluster = cluster
        web.deployer = deployer
        _connect_signals()
        return app
