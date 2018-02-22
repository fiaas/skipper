#!/usr/bin/env python
# -*- coding: utf-8

from fiaas_skipper import web


def test_dummy():
    assert web.hello_world() == "Hello World!"
