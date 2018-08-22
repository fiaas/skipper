#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import json
import logging
import os

import yaml
from k8s import config as k8s_config

from fiaas_skipper.deploy import StatusTracker
from fiaas_skipper.update import AutoUpdater
from .config import Configuration
from .deploy import CrdDeployer, TprDeployer, ReleaseChannelFactory, CrdBootstrapper, TprBootstrapper, \
    FiaasApplication, PaasbetaApplication
from .deploy.channel import FakeReleaseChannelFactory
from .deploy.cluster import Cluster
from .logsetup import init_logging
from .web import create_webapp


class Main(object):
    def __init__(self, webapp, config):
        self._webapp = webapp
        self._config = config

    def run(self):
        # Run web-app in main thread
        self._webapp.run("0.0.0.0", self._config.port)


def init_k8s_client(config):
    k8s_config.api_server = config.api_server
    k8s_config.api_token = config.api_token
    if config.api_cert:
        k8s_config.verify_ssl = config.api_cert
    else:
        k8s_config.verify_ssl = not config.debug
    if config.client_cert:
        k8s_config.cert = (config.client_cert, config.client_key)
    k8s_config.debug = config.debug
    k8s_config.timeout = 60


def _load_spec_config(spec_file):
    with open(spec_file, 'r') as stream:
        return yaml.safe_load(stream)


def _read_file(spec_file):
    with open(spec_file) as f:
        return f.read()


def main():
    cfg = Configuration()
    init_logging(cfg)
    init_k8s_client(cfg)
    log = logging.getLogger(__name__)
    try:
        log.info("fiaas-skipper starting with configuration {!r}".format(cfg))
        cluster = Cluster()
        if cfg.release_channel_metadata:
            log.debug("!!Using hardcoded release channel metadata {!r}".format(cfg.release_channel_metadata))
            spec = _read_file(cfg.release_channel_metadata_spec)
            release_channel_factory = FakeReleaseChannelFactory(json.loads(cfg.release_channel_metadata), spec)
        else:
            release_channel_factory = ReleaseChannelFactory(cfg.baseurl)
        spec_config_extension = None
        if os.path.isfile(cfg.spec_file_override):
            try:
                spec_config_extension = _load_spec_config(cfg.spec_file_override)
                log.debug("Loaded spec config extension from file {!r}".format(cfg.spec_file_override))
            except yaml.YAMLError:
                log.exception("Unable to load spec config extension file {!r} using defaults"
                              .format(cfg.spec_file_override))
        if cfg.enable_crd_support:
            application = FiaasApplication
            deployer = CrdDeployer(cluster=cluster, release_channel_factory=release_channel_factory,
                                   bootstrap=CrdBootstrapper(), spec_config_extension=spec_config_extension)
        elif cfg.enable_tpr_support:
            application = PaasbetaApplication
            deployer = TprDeployer(cluster=cluster, release_channel_factory=release_channel_factory,
                                   bootstrap=TprBootstrapper(), spec_config_extension=spec_config_extension)
        # Do period checking of deployment status across all namespaces
        status_tracker = StatusTracker(cluster=cluster, application=application)
        status_tracker.start()
        if not cfg.disable_autoupdate:
            updater = AutoUpdater(release_channel_factory=release_channel_factory, deployer=deployer,
                                  status=status_tracker)
            updater.daemon = True
            updater.start()
        else:
            log.debug("Auto updates disabled")
        webapp = create_webapp(deployer, cluster, release_channel_factory, status_tracker)
        Main(webapp=webapp, config=cfg).run()
    except BaseException:
        log.exception("General failure! Inspect traceback and make the code better!")


if __name__ == "__main__":
    main()
