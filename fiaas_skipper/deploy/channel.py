#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging
from collections import namedtuple

import requests

LOG = logging.getLogger(__name__)


ReleaseChannel = namedtuple("ReleaseChannel", ["name", "tag", "metadata", "spec"])


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
            LOG.error("No spec url specified")
            raise ValueError("Channel metadata contained no config URL")
        LOG.debug("Loading spec from channel metadata: " + url)
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.text


class FakeReleaseChannelFactory(object):
    """ Used for hardcoding release channel information """

    def __init__(self, metadata, spec=None):
        self._metadata = metadata
        self._spec = spec

    def __call__(self, name, tag):
        return ReleaseChannel(name, tag, metadata=self._metadata, spec=self._spec)
