#!/usr/bin/env python
# -*- coding: utf-8

import logging
from threading import Thread

import time

LOG = logging.getLogger(__name__)
CHECK_UPDATE_INTERVAL = 600
TAGS = ('latest', 'stable')


class AutoUpdater(Thread):
    def __init__(self, release_channel_factory, deployer):
        Thread.__init__(self)
        self._release_channel_factory = release_channel_factory
        self._deployer = deployer
        self._images = {}

    def check_updates(self):
        """
        Check if there are new versions available.
        If there are the deployer is triggered.
        """
        LOG.debug("Checking for new updates")
        found_update = False
        for t in TAGS:
            channel = self._release_channel_factory('fiaas-deploy-daemon', t)
            if self._new_version_available(channel):
                LOG.debug("Detected new update for {} ({})".format(t, channel.metadata['image']))
                found_update = True
            self._images[t] = channel.metadata['image']
        if found_update:
            # TODO perhaps this could be made smarter by inspecting namespaces
            self._deployer.deploy()

    def _new_version_available(self, channel):
        return self._images.get(channel.tag, channel.metadata['image']) != channel.metadata['image']

    def check_bootstrap(self):
        """
        Check if there are any namespaces that need bootstrapping.
        If that is the case the deployer is triggered.
        """
        LOG.debug("Checking for namespaces that need bootstrapping")
        need_bootstrap = [s.namespace for s in self._deployer.status() if s.status == 'NOT_FOUND']
        if need_bootstrap:
            LOG.debug("Detected namespaces {} need bootstrapping".format(', '.join(need_bootstrap)))
            self._deployer.deploy(namespaces=need_bootstrap)

    def run(self):
        while True:
            self.check_bootstrap()
            self.check_updates()
            time.sleep(CHECK_UPDATE_INTERVAL)
