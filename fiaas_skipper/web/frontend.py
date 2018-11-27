#!/usr/bin/env python
# -*- coding: utf-8
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
        Link('Deploy using PaaS', 'https://confluence.schibsted.io/display/SPTINF/Deploy+using+PaaS'),
        #Separator(),
        #Text('Bootstrap'),
        #Link('Getting started', 'http://fiaas/getting-started/'),
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
