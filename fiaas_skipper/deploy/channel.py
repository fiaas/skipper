#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging

import requests

LOG = logging.getLogger(__name__)


class ReleaseChannel(object):
    def __init__(self, name, tag, metadata, spec=None):
        self.name = name
        self.tag = tag
        self.metadata = metadata
        self.spec = spec


class ReleaseChannelFactory(object):
    def __init__(self, baseurl):
        self._baseurl = baseurl

    def __call__(self, name, tag):
        r = requests.get('%s/%s/%s.json' % (self._baseurl, name, tag))
        LOG.debug('Retrieving meta data for %s/%s/%s.json' % (self._baseurl, name, tag))
        metadata = r.json()
        spec = self._get_spec(metadata.get('spec', None))
        return ReleaseChannel(name, tag, metadata=metadata, spec=spec)

    @staticmethod
    def _get_spec(url):
        """Load spec file yaml from url"""
        if not url:
            LOG.debug("No spec url specified")
            return None
        LOG.debug("Loading spec from channel metadata: " + url)
        return requests.get(url).text


class FakeReleaseChannelFactory(object):
    """ Used for hardcoding release channel information """

    def __init__(self, metadata, spec=None):
        self._metadata = metadata
        self._spec = spec

    def __call__(self, name, tag):
        return ReleaseChannel(name, tag, metadata=self._metadata, spec=self._spec)
