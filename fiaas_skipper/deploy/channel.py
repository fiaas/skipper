#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging

import requests

LOG = logging.getLogger(__name__)


class ReleaseChannel(object):
    def __init__(self, name, tag, metadata):
        self.name = name
        self.tag = tag
        self.metadata = metadata


class ReleaseChannelFactory(object):
    def __init__(self, baseurl):
        self._baseurl = baseurl

    def __call__(self, name, tag):
        r = requests.get('%s/%s/%s.json' % (self._baseurl, name, tag))
        LOG.debug('Retrieving meta data for %s/%s/%s.json' % (self._baseurl, name, tag))
        return ReleaseChannel(name, tag, metadata=r.json())
