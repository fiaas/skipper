#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging

from .types import PaasbetaApplication, PaasbetaApplicationSpec
from ..deploy import Deployer, StatusTracker

LOG = logging.getLogger(__name__)


class TprDeployer(Deployer):
    def _deploy(self, deployment_config, channel, spec_config):
        LOG.info("Deploying %s to %s", deployment_config.name, deployment_config.namespace)
        pba = PaasbetaApplication.get_or_create(metadata=self._create_metadata(deployment_config))
        pba.spec = self._create_paasbetaapplicationspec(name=deployment_config.name,
                                                        image=channel.metadata['image'],
                                                        spec_config=spec_config)
        pba.save()

    def _create_paasbetaapplicationspec(self, name, image, spec_config):
        return PaasbetaApplicationSpec(application=name, image=image, config=spec_config)

    def _application(self):
        return PaasbetaApplication


class TprStatusTracker(StatusTracker):
    def _application(self):
        return PaasbetaApplication
