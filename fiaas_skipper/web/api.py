#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import json
import threading

from flask import Blueprint, make_response, request

from ..deploy import DeploymentConfigStatus
from ..web import request_histogram

api = Blueprint("api", __name__)

status_histogram = request_histogram.labels("status")
deploy_histogram = request_histogram.labels("deploy")


@api.route('/api/status')
@status_histogram.time()
def status():
    deployment_config_statuses = api.cluster.find_deployment_config_statuses('fiaas-deploy-daemon')
    return make_response(json.dumps(deployment_config_statuses, default=_encode), 200)


def _encode(obj):
    if isinstance(obj, DeploymentConfigStatus):
        return obj.__dict__
    return obj


@api.route('/api/deploy', methods=['POST'])
@deploy_histogram.time()
def deploy():
    if request.get_json() and 'namespaces' in request.get_json():
        threading.Thread(target=api.deployer.deploy, kwargs={'namespaces': request.get_json()['namespaces']}).start()
    else:
        threading.Thread(target=api.deployer.deploy).start()
    return make_response('', 200)
