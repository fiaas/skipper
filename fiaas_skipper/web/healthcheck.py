#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

from flask import Blueprint, make_response

healthcheck = Blueprint("healthcheck", __name__)


@healthcheck.route('/healthz')
def healthz():
    if healthcheck.status.is_alive():
        return make_response('', 200)
    else:
        return make_response('', 500)
