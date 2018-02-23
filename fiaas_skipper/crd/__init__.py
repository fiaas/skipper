#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging

from k8s.models.common import ObjectMeta
from k8s.models.custom_resource_definition import CustomResourceDefinition, CustomResourceDefinitionSpec, CustomResourceDefinitionNames

LOG = logging.getLogger(__name__)


def _create(kind, plural, short_names, group):
    name = "%s.%s" % (plural, group)
    metadata = ObjectMeta(name=name)
    names = CustomResourceDefinitionNames(kind=kind, plural=plural, shortNames=short_names)
    spec = CustomResourceDefinitionSpec(group=group, names=names, version="v1")
    definition = CustomResourceDefinition.get_or_create(metadata=metadata, spec=spec)
    definition.save()
    LOG.info("Created CustomResourceDefinition with name %s", name)


def create_custom_resource_definitions():
    _create("Application", "applications", ("app", "fa"), "fiaas.schibsted.io")
    _create("Status", "statuses", ("status", "fs"), "fiaas.schibsted.io")
