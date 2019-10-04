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

import logging

import pkg_resources
from dominate.tags import img
from flask import Blueprint, render_template
from flask_nav.elements import Navbar, View, Subgroup, Link, Text

from fiaas_skipper.deploy.channel import ReleaseChannelError
from .nav import nav

LOG = logging.getLogger(__name__)
FIAAS_VERSION = pkg_resources.require("fiaas_skipper")[0].version

frontend = Blueprint('frontend', __name__)

branding = img(src='/static/fiaas_small.png')

nav.register_element('frontend_top', Navbar(
    branding,
    View('Home', '.index'),
    View('Status', '.status'),
    View('Deploy', '.deploy'),
    Subgroup(
        'Docs',
        Link('Getting started', 'https://fiaas.github.io/'),
    ),
    Text('Using FIAAS {}'.format(FIAAS_VERSION)), ))


@frontend.route('/')
def index():
    return render_template('index.html')


@frontend.route('/status')
def status():
    versions = {}
    for tag in ("stable", "latest"):
        try:
            channel = frontend.release_channel_factory("fiaas-deploy-daemon", tag)
            image = channel.metadata["image"]
            version = image.split(":")[-1]
        except ReleaseChannelError:
            LOG.exception("Unable to determine version for tag: %s" % tag)
            version = "unavailable"
        versions[tag] = version
    return render_template('status.html', versions=versions)


@frontend.route('/deploy')
def deploy():
    return render_template('deploy.html')
