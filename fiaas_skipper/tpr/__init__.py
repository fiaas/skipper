#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging

from k8s.models.common import ObjectMeta
from k8s.models.third_party_resource import ThirdPartyResource, APIVersion


LOG = logging.getLogger(__name__)


def create_third_party_resource_definitions():
    metadata = ObjectMeta(name="paasbeta-application.schibsted.io")
    paasbeta_application_resource = ThirdPartyResource.get_or_create(
        metadata=metadata, description='A paas application definition', versions=[APIVersion(name='v1beta')])
    paasbeta_application_resource.save()
    LOG.info("Created ThirdPartyResource with name PaasbetaApplication")
    metadata = ObjectMeta(name="paasbeta-status.schibsted.io")
    paasbeta_status_resource = ThirdPartyResource.get_or_create(
        metadata=metadata, description='A paas application status', versions=[APIVersion(name='v1beta')])
    paasbeta_status_resource.save()
    LOG.info("Created ThirdPartyResource with name PaasbetaStatus")
