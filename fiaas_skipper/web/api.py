#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import json
import logging
import threading

from flask import Blueprint, make_response, request

from ..deploy.cluster import DeploymentConfigStatus
from ..web import request_histogram

LOG = logging.getLogger(__name__)

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
        threading.Thread(target=_deploy, kwargs={'namespaces': request.get_json()['namespaces']}).start()
    else:
        threading.Thread(target=_deploy).start()
    return make_response('', 200)


def _deploy(namespaces=None):
    try:
        api.deployer.deploy(namespaces=namespaces)
    except Exception:
        logging.exception("Unexpected failure when deploying")
