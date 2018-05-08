#!/usr/bin/env python
# -*- coding: utf-8

import mock
import pytest


@pytest.fixture(autouse=True)
def get():
    with mock.patch('k8s.client.Client.get') as m:
        yield m
