#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging

from .types import PaasbetaApplication, PaasbetaApplicationSpec
from ..deploy import Deployer, default_config_template

LOG = logging.getLogger(__name__)


class TprDeployer(Deployer):
    def _deploy(self, deployment_config, channel):
        LOG.info("Deploying %s to %s", deployment_config.name, deployment_config.namespace)
        pba = PaasbetaApplication(metadata=self._create_metadata(deployment_config),
                                  spec=self._create_paasbetaapplicationspec(name=deployment_config.name,
                                                                            image=channel.metadata['image']))
        pba.save()

    def _create_paasbetaapplicationspec(self, name, image):
        return PaasbetaApplicationSpec(application=name, image=image, config=default_config_template)
