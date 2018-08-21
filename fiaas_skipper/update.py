#!/usr/bin/env python
# -*- coding: utf-8

import logging
from threading import Thread

import time

LOG = logging.getLogger(__name__)
CHECK_UPDATE_INTERVAL = 60


class AutoUpdater(Thread):
    def __init__(self, release_channel_factory, deployer):
        Thread.__init__(self)
        self._release_channel_factory = release_channel_factory
        self._deployer = deployer

    def check_updates(self):
        """
        Check if there are new versions available.
        If there are the deployer is triggered.
        """
        LOG.debug("Checking for new updates")
        for channel_name in self._channels():
            channel = self._release_channel_factory('fiaas-deploy-daemon', channel_name)
            update_namespaces = self._update_namespaces(channel)
            if update_namespaces:
                LOG.debug("Detected new update for {} ({})".format((',').join(update_namespaces),
                                                                   channel.metadata['image']))
                self._deployer.deploy(namespaces=update_namespaces)

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
        time.sleep(60)  # Delay at start to allow status to have been populated
        while True:
            self.check_bootstrap()
            self.check_updates()
            time.sleep(CHECK_UPDATE_INTERVAL)

    def _channels(self):
        return set([s.channel for s in self._deployer.status()])

    def _update_namespaces(self, channel):
        matched = [t for t in self._deployer.status() if t.channel == channel.tag]
        return set([s.namespace for s in matched if s.version != channel.metadata['image'].split(':')[1]])
