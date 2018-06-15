#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import json
import logging
import os

import yaml
from k8s import config as k8s_config

from .config import Configuration
from .deploy import CrdDeployer, TprDeployer, ReleaseChannelFactory, CrdBootstrapper, TprBootstrapper
from .deploy.channel import FakeReleaseChannelFactory
from .deploy.cluster import Cluster
from .logsetup import init_logging
from .web import create_webapp


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


def create_app():
    cfg = Configuration()
    init_logging(cfg)
    init_k8s_client(cfg)
    log = logging.getLogger(__name__)
    log.info("fiaas-skipper starting with configuration {!r}".format(cfg))
    cluster = Cluster()
    if cfg.release_channel_metadata:
        log.debug("!!Using hardcoded release channel metadata {!r}".format(cfg.release_channel_metadata))
        release_channel_factory = FakeReleaseChannelFactory(json.loads(cfg.release_channel_metadata))
    else:
        release_channel_factory = ReleaseChannelFactory(cfg.baseurl)
    spec_config = None
    if os.path.isfile(cfg.spec_file):
        try:
            spec_config = _load_spec_config(cfg.spec_file)
            log.debug("Loaded spec config from file {!r}".format(cfg.spec_file))
        except yaml.YAMLError:
            log.exception("Unable to load spec config file {!r} using defaults".format(cfg.spec_file))
    if cfg.enable_crd_support:
        deployer = CrdDeployer(cluster=cluster, release_channel_factory=release_channel_factory,
                               bootstrap=CrdBootstrapper(), spec_config=spec_config)
    elif cfg.enable_tpr_support:
        deployer = TprDeployer(cluster=cluster, release_channel_factory=release_channel_factory,
                               bootstrap=TprBootstrapper(), spec_config=spec_config)
    else:
        raise RuntimeError("Invalid configuration: Either --enable-tpr-support or --enable-crd-support must be set")
    return create_webapp(deployer, cluster), cfg


app, cfg = create_app()

if __name__ == "__main__":
    log = logging.getLogger(__name__)
    try:
        app.run("0.0.0.0", cfg.port)
    except BaseException:
        log.exception("General failure! Inspect traceback and make the code better!")
