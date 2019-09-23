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
