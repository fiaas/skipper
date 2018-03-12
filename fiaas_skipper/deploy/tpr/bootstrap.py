#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging

from k8s.models.common import ObjectMeta
from k8s.models.third_party_resource import ThirdPartyResource, APIVersion

from fiaas_skipper.deploy.bootstrap import Bootstrapper

LOG = logging.getLogger(__name__)


class TprBootstrapper(Bootstrapper):
    def __init__(self):
        def bootstrap():
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
        bootstrap()
        super(TprBootstrapper, self).__init__(cmd_args=["--enable-tpr-support"])
