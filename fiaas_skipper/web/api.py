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

import json
import logging
import threading

from flask import Blueprint, make_response, request

from ..deploy.deploy import DeploymentStatus
from ..web import request_histogram

LOG = logging.getLogger(__name__)

api = Blueprint("api", __name__)

status_histogram = request_histogram.labels("status")
deploy_histogram = request_histogram.labels("deploy")


@api.route('/api/status')
@status_histogram.time()
def status():
    deployment_statuses = api.status()
    return make_response(json.dumps(deployment_statuses, default=_encode), 200)


def _encode(obj):
    if isinstance(obj, DeploymentStatus):
        return obj.__dict__
    return obj


def _force_bootstrap(request):
    if request.get_json() and 'force_bootstrap' in request.get_json():
        return request.get_json()['force_bootstrap']
    return False


def _namespaces(request):
    if request.get_json() and 'namespaces' in request.get_json():
        return request.get_json()['namespaces']


@api.route('/api/deploy', methods=['POST'])
@deploy_histogram.time()
def deploy():
    namespaces = _namespaces(request)
    force_bootstrap = _force_bootstrap(request)
    threading.Thread(target=_deploy, kwargs={'namespaces': namespaces,
                                             'force_bootstrap': force_bootstrap}).start()
    return make_response('', 200)


def _deploy(namespaces=None, force_bootstrap=False):
    try:
        api.deployer.deploy(namespaces=namespaces, force_bootstrap=force_bootstrap)
    except Exception:
        logging.exception("Unexpected failure when deploying")
