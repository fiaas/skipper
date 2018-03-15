#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging

from .types import PaasbetaApplication, PaasbetaApplicationSpec
from ..deploy import Deployer, generate_config, default_config_template

LOG = logging.getLogger(__name__)


class TprDeployer(Deployer):
    def _deploy(self, deployment_config, channel):
        LOG.info("Deploying %s to %s", deployment_config.name, deployment_config.namespace)
        pba = PaasbetaApplication(metadata=self._create_metadata(deployment_config),
                                  spec=self._create_paasbetaapplicationspec(name=deployment_config.name,
                                                                            namespace=deployment_config.namespace,
                                                                            image=channel.metadata['image']))
        pba.save()

    def _create_paasbetaapplicationspec(self, name, namespace, image):
        config = generate_config(template=default_config_template,
                                 namespace=namespace,
                                 ingress_suffix=self._ingress_suffix)
        return PaasbetaApplicationSpec(application=name, image=image, config=config)
