#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import json

from flask import Blueprint, make_response

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
    api.deployer.deploy()
    return make_response('', 200)
