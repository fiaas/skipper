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

from gevent import monkey

monkey.patch_all()  # NOQA

import json
import logging
import os
import signal

import yaml
from k8s import config as k8s_config

from fiaas_skipper.deploy import StatusTracker
from fiaas_skipper.update import AutoUpdater
from .config import Configuration
from .deploy import CrdDeployer, ReleaseChannelFactory, CrdBootstrapper, \
    FiaasApplication
from .deploy.channel import FakeReleaseChannelFactory
from .deploy.cluster import Cluster
from .logsetup import init_logging
from .web import create_webapp

from gevent.pywsgi import WSGIServer, LoggingLogAdapter

LOG = logging.getLogger(__name__)


class ExitOnSignal(Exception):
    pass


def signal_handler(signum, frame):
    signame = signal.Signals(signum).name
    LOG.critical(f"Received signal {signame}({signum}), exiting")
    raise ExitOnSignal()


def init_k8s_client(config, log):
    if config.client_cert:
        k8s_config.cert = (config.client_cert, config.client_key)

    if config.api_token:
        k8s_config.api_token = config.api_token
    else:
        # use default in-cluster config if api_token is not explicitly set
        try:
            # sets api_token_source and verify_ssl
            k8s_config.use_in_cluster_config()
        except IOError as e:
            if not config.client_cert:
                log.warn("No apiserver auth config was specified, and in-cluster config could not be set up: " + str(e))

    # if api_cert or debug is explicitly set, override in-cluster config setting (if used)
    if config.api_cert:
        k8s_config.verify_ssl = config.api_cert
    elif config.debug:
        k8s_config.verify_ssl = not config.debug

    k8s_config.api_server = config.api_server
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
    log = logging.getLogger(__name__)
    init_k8s_client(cfg, log)
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, signal_handler)
    try:
        log.info("fiaas-skipper starting with configuration {!r}".format(cfg))
        cluster = Cluster()
        if cfg.release_channel_metadata:
            log.warning("!!Using hardcoded release channel metadata {!r}".format(cfg.release_channel_metadata))
            log.warning("!!Reading hardcoded release channel metadata spec file from {!r}".format(
                cfg.release_channel_metadata_spec))
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
        deployer = CrdDeployer(cluster=cluster, release_channel_factory=release_channel_factory,
                               bootstrap=CrdBootstrapper(), spec_config_extension=spec_config_extension,
                               rbac=cfg.manage_rbac)
        # Do period checking of deployment status across all namespaces
        status_tracker = StatusTracker(cluster=cluster, application=FiaasApplication,
                                       interval=cfg.status_update_interval)
        status_tracker.start()
        if not cfg.disable_autoupdate:
            updater = AutoUpdater(release_channel_factory=release_channel_factory, deployer=deployer,
                                  status=status_tracker)
            updater.start()
        else:
            log.debug("Auto updates disabled")
        webapp = create_webapp(deployer, cluster, release_channel_factory, status_tracker)
        log = LoggingLogAdapter(LOG, logging.DEBUG)
        error_log = LoggingLogAdapter(LOG, logging.ERROR)
        # Run web-app in main thread
        http_server = WSGIServer(("", cfg.port), webapp, log=log, error_log=error_log)
        http_server.serve_forever()
    except ExitOnSignal:
        pass
    except BaseException:
        log.exception("General failure! Inspect traceback and make the code better!")


if __name__ == "__main__":
    main()
