#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

from flask import Blueprint, make_response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from ..web import request_histogram

metrics = Blueprint("metrics", __name__)

metrics_histogram = request_histogram.labels("metrics")


@metrics.route("/_/metrics")
@metrics_histogram.time()
def internal_metrics():
    resp = make_response(generate_latest())
    resp.mimetype = CONTENT_TYPE_LATEST
    return resp
