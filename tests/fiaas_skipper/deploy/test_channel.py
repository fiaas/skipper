#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

from fiaas_skipper.deploy import ReleaseChannelFactory

METADATA = {"key1": "value1", "spec": "http://example.com/config.yaml"}
CONFIG = """
version: 3
"""


class TestReleaseChannelFactory(object):
    def test_fetch_metadata(self, requests_mock):
        requests_mock.get("http://example.com/name/tag.json", json=METADATA)
        requests_mock.get("http://example.com/config.yaml", text=CONFIG)

        factory = ReleaseChannelFactory(baseurl="http://example.com")
        rc = factory('name', 'tag')
        assert rc.name == 'name'
        assert rc.tag == 'tag'
        assert rc.metadata == METADATA
        assert rc.spec == CONFIG
