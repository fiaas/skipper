#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging

from .types import PaasbetaApplication, PaasbetaApplicationSpec
from ..deploy import Deployer
from ...deploy import default_config

LOG = logging.getLogger(__name__)


class TprDeployer(Deployer):
    def _deploy(self, deployment_config, channel):
        LOG.info("Deploying %s to %s", deployment_config.name, deployment_config.namespace)
        pba = PaasbetaApplication(metadata=self._create_metadata(deployment=deployment_config),
                                  spec=self._create_paasbetaapplicationspec(deployment_config, channel.metadata['image']))
        pba.save()

    @staticmethod
    def _create_paasbetaapplicationspec(deployment_config, image):
        return PaasbetaApplicationSpec(application=deployment_config.name, image=image, config=default_config)
