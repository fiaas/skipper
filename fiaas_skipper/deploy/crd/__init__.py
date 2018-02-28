#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging

import pinject
from k8s.models.common import ObjectMeta
from k8s.models.custom_resource_definition import CustomResourceDefinition, CustomResourceDefinitionSpec, \
    CustomResourceDefinitionNames

from .deployer import CrdDeployer

LOG = logging.getLogger(__name__)


class CrdBindings(pinject.BindingSpec):
    def configure(self, bind):
        bind("deployer", to_class=CrdDeployer)
        _create_custom_resource_definitions()


def _create(kind, plural, short_names, group):
    name = "%s.%s" % (plural, group)
    metadata = ObjectMeta(name=name)
    names = CustomResourceDefinitionNames(kind=kind, plural=plural, shortNames=short_names)
    spec = CustomResourceDefinitionSpec(group=group, names=names, version="v1")
    definition = CustomResourceDefinition.get_or_create(metadata=metadata, spec=spec)
    definition.save()
    LOG.info("Created CustomResourceDefinition with name %s", name)


def _create_custom_resource_definitions():
    _create("Application", "applications", ("app", "fa"), "fiaas.schibsted.io")
    _create("Status", "statuses", ("status", "fs"), "fiaas.schibsted.io")
