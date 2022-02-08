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

from __future__ import absolute_import, unicode_literals

import mock
from requests import Response

from k8s.client import NotFound

from fiaas_skipper.deploy.crd.crd_resources_syncer_apiextensionsv1beta1 import \
    CrdResourcesSyncerApiextensionsV1Beta1


EXPECTED_APPLICATION = {
    'metadata': {
        'namespace': 'default',
        'name': 'applications.fiaas.schibsted.io',
        'ownerReferences': [],
        'finalizers': [],
    },
    'spec': {
        'version': 'v1',
        'group': 'fiaas.schibsted.io',
        'names': {
            'shortNames': ['app', 'fa'],
            'kind': 'Application',
            'plural': 'applications'
        }
    }
}


EXPECTED_STATUS = {
    'metadata': {
        'namespace': 'default',
        'name': 'application-statuses.fiaas.schibsted.io',
        'ownerReferences': [],
        'finalizers': [],
    },
    'spec': {
        'version': 'v1',
        'group': 'fiaas.schibsted.io',
        'names': {
            'shortNames': ['status', 'appstatus', 'fs'],
            'kind': 'ApplicationStatus',
            'plural': 'application-statuses'
        }
    }
}


class TestCrdResourcesSyncerV1beta1(object):
    def test_creates_crd_resources(self, post, get):
        get.side_effect = NotFound("Something")

        def make_response(data):
            mock_response = mock.create_autospec(Response)
            mock_response.json.return_value = data
            return mock_response

        post.side_effect = [make_response(EXPECTED_APPLICATION), make_response(EXPECTED_STATUS)]

        CrdResourcesSyncerApiextensionsV1Beta1.update_crd_resources()

        calls = [
            mock.call("/apis/apiextensions.k8s.io/v1beta1/customresourcedefinitions/", EXPECTED_APPLICATION),
            mock.call("/apis/apiextensions.k8s.io/v1beta1/customresourcedefinitions/", EXPECTED_STATUS)
        ]
        assert post.call_args_list == calls

    def test_updates_crd_resources_when_found(self, put, get):
        def make_response(data):
            mock_response = mock.create_autospec(Response)
            mock_response.json.return_value = data
            return mock_response

        get.side_effect = [make_response(EXPECTED_APPLICATION), make_response(EXPECTED_STATUS)]
        put.side_effect = [make_response(EXPECTED_APPLICATION), make_response(EXPECTED_STATUS)]

        CrdResourcesSyncerApiextensionsV1Beta1.update_crd_resources()

        crd_api_uri = "/apis/apiextensions.k8s.io/v1beta1/customresourcedefinitions"
        calls = [
            mock.call("{crd_api_uri}/applications.fiaas.schibsted.io".format(crd_api_uri=crd_api_uri),
                      EXPECTED_APPLICATION),
            mock.call("{crd_api_uri}/application-statuses.fiaas.schibsted.io".format(crd_api_uri=crd_api_uri),
                      EXPECTED_STATUS)
        ]
        assert put.call_args_list == calls
