# #!/usr/bin/env python
# # -*- coding: utf-8
from unittest import TestCase

import mock

from fiaas_skipper.deploy import ReleaseChannelFactory

metadata = {"key1": "value1"}


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if args[0] == 'http://localhost/name/tag.json':
        return MockResponse(metadata, 200)
    return MockResponse(None, 404)


class TestReleaseChannelFactory(TestCase):
    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_fetch_metadata(self, mock_get):
        factory = ReleaseChannelFactory(baseurl="http://localhost")
        rc = factory('name', 'tag')
        assert rc.name == 'name'
        assert rc.tag == 'tag'
        assert rc.metadata == metadata
