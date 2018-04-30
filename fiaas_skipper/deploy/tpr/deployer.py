#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging

from .types import PaasbetaApplication, PaasbetaApplicationSpec
from ..deploy import Deployer

LOG = logging.getLogger(__name__)


class TprDeployer(Deployer):
    def _deploy(self, deployment_config, channel, config):
        LOG.info("Deploying %s to %s", deployment_config.name, deployment_config.namespace)
        pba = PaasbetaApplication(metadata=self._create_metadata(deployment_config),
                                  spec=self._create_paasbetaapplicationspec(name=deployment_config.name,
                                                                            image=channel.metadata['image'],
                                                                            config=config))
        pba.save()

    def _create_paasbetaapplicationspec(self, name, image, config):
        return PaasbetaApplicationSpec(application=name, image=image, config=config)
