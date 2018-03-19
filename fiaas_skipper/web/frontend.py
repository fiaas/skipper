#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

from flask import Blueprint, render_template
from flask_nav.elements import Navbar, View, Subgroup, Link, Text

from dominate.tags import img

from .nav import nav

import pkg_resources

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
    return render_template('status.html')


@frontend.route('/deploy')
def deploy():
    return render_template('deploy.html')
