#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import pytest
import requests

from fiaas_skipper.deploy import ReleaseChannelFactory
from fiaas_skipper.deploy.channel import ReleaseChannelError


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

    def test_fetch_metadata_raises_exception_on_connection_error(self, requests_mock):
        requests_mock.get("http://example.com/name/tag.json", exc=requests.exceptions.ConnectionError)

        factory = ReleaseChannelFactory(baseurl="http://example.com")
        with pytest.raises(ReleaseChannelError):
            factory('name', 'tag')

    def test_fetch_metadata_raises_exception_on_not_found(self, requests_mock):
        requests_mock.get("http://example.com/name/tag.json", text='Not Found', status_code=404)

        factory = ReleaseChannelFactory(baseurl="http://example.com")
        with pytest.raises(ReleaseChannelError):
            factory('name', 'tag')

    def test_fetch_metadata_raises_exception_when_unable_to_get_config(self, requests_mock):
        requests_mock.get("http://example.com/name/tag.json", json=METADATA)
        requests_mock.get("http://example.com/config.yaml", text='Not Found', status_code=404)

        factory = ReleaseChannelFactory(baseurl="http://example.com")
        with pytest.raises(ReleaseChannelError):
            factory('name', 'tag')
