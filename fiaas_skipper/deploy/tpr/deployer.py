#!/usr/bin/env python
# -*- coding: utf-8
import logging

from .types import PaasbetaApplication, PaasbetaApplicationSpec
from ..deploy import Deployer

LOG = logging.getLogger(__name__)


class TprDeployer(Deployer):
    def _deploy(self, deployment, channel):
        LOG.info("Deploying %s to %s", deployment.name, deployment.namespace)
        pba = PaasbetaApplication(metadata=self._create_metadata(deployment=deployment),
                                  spec=self._create_paasbetaapplicationspec(deployment, channel.image))
        pba.save()

    @staticmethod
    def _create_paasbetaapplicationspec(deployment, image):
        return PaasbetaApplicationSpec(application=deployment.name, image=image, config={})
