#!/usr/bin/env python
# -*- coding: utf-8
import logging

import pinject
import requests

LOG = logging.getLogger(__name__)


class ReleaseChannel(object):
    @pinject.copy_args_to_public_fields
    def __init__(self, name, tag, metadata):
        pass


class ReleaseChannelFactory(object):
    @pinject.copy_args_to_internal_fields
    def __init__(self, baseurl):
        pass

    def __call__(self, name, tag):
        r = requests.get('%s/%s/%s.json' % (self._baseurl, name, tag))
        LOG.debug('Retrieving meta data for %s/%s/%s.json' % (self._baseurl, name, tag))
        return ReleaseChannel(name, tag, metadata=r.json())
