#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging
from Queue import Queue

import pinject
import requests
from k8s import config as k8s_config

from .config import Configuration
from .logsetup import init_logging
from .web import WebBindings


class MainBindings(pinject.BindingSpec):
    def __init__(self, config):
        self._config = config
        self._deploy_queue = Queue()

    def configure(self, bind):
        bind("config", to_instance=self._config)

    def provide_session(self, config):
        session = requests.Session()
        if config.proxy:
            session.proxies = {scheme: config.proxy for scheme in (
                "http",
                "https"
            )}
        return session


class Main(object):
    @pinject.copy_args_to_internal_fields
    def __init__(self, webapp, config):
        pass

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
        log.info("fiaas-deploy-daemon starting with configuration {!r}".format(cfg))
        binding_specs = [
            MainBindings(cfg),
            WebBindings(),
        ]
        obj_graph = pinject.new_object_graph(modules=None, binding_specs=binding_specs)
        obj_graph.provide(Main).run()
    except BaseException:
        log.exception("General failure! Inspect traceback and make the code better!")


if __name__ == "__main__":
    main()
