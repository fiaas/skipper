#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

from flask import Blueprint, make_response

healthcheck = Blueprint("healthcheck", __name__)


@healthcheck.route('/healthz')
def healthz():
    return make_response('', 200)
