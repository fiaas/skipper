#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging

from .types import FiaasApplicationSpec, FiaasApplication
from ..deploy import Deployer

LOG = logging.getLogger(__name__)


class CrdDeployer(Deployer):
    def _deploy(self, deployment_config, channel, spec_config):
        LOG.info("Deploying %s to %s", deployment_config.name, deployment_config.namespace)
        fdd_app = FiaasApplication.get_or_create(metadata=self._create_metadata(deployment_config))
        fdd_app.spec = self._create_application_spec(name=deployment_config.name,
                                                     image=channel.metadata['image'],
                                                     spec_config=spec_config)
        fdd_app.save()

    def _create_application_spec(self, name, image, spec_config):
        return FiaasApplicationSpec(application=name, image=image, config=spec_config)
