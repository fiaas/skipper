#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging

from k8s import config as k8s_config

from .config import Configuration
from .deploy import Cluster, CrdDeployer, TprDeployer, ReleaseChannelFactory, CrdBootstrapper, TprBootstrapper
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


def main():
    cfg = Configuration()
    init_logging(cfg)
    init_k8s_client(cfg)
    log = logging.getLogger(__name__)
    try:
        log.info("fiaas-skipper starting with configuration {!r}".format(cfg))
        cluster = Cluster()
        release_channel_factory = ReleaseChannelFactory(cfg.baseurl)
        if cfg.enable_crd_support:
            deployer = CrdDeployer(cluster=cluster, release_channel_factory=release_channel_factory,
                                   bootstrap=CrdBootstrapper())
        elif cfg.enable_tpr_support:
            deployer = TprDeployer(cluster=cluster, release_channel_factory=release_channel_factory,
                                   bootstrap=TprBootstrapper())
        webapp = create_webapp(deployer, cluster)
        Main(webapp=webapp, config=cfg).run()
    except BaseException:
        log.exception("General failure! Inspect traceback and make the code better!")


if __name__ == "__main__":
    main()
