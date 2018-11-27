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
        LOG.debug('Retrieving meta data for %s/%s/%s.json' % (self._baseurl, name, tag))
        try:
            r = requests.get('%s/%s/%s.json' % (self._baseurl, name, tag))
            r.raise_for_status()
            metadata = r.json()
            spec = self._get_spec(metadata.get('spec', None))
            return ReleaseChannel(name, tag, metadata=metadata, spec=spec)
        except requests.exceptions.RequestException as e:
            raise ReleaseChannelError("Unable to retrieve metadata") from e

    @staticmethod
    def _get_spec(url):
        """Load spec file yaml from url"""
        if not url:
            raise ReleaseChannelError("Channel metadata contained no config URL")
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


class ReleaseChannelError(Exception):
    pass
