#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging

from k8s.client import ClientError

from .types import FiaasApplicationSpec, FiaasApplication
from ..deploy import Deployer
from ...deploy import default_config

LOG = logging.getLogger(__name__)


class CrdDeployer(Deployer):
    def _deploy(self, deployment_config, channel):
        LOG.info("Deploying %s to %s", deployment_config.name, deployment_config.namespace)
        try:
            fdd_app = FiaasApplication(metadata=self._create_metadata(deployment_config=deployment_config),
                                       spec=self._create_application_spec(deployment_config, image=channel.metadata['image']))
            fdd_app.save()
        except ClientError as e:
            if e.response.json()['reason'] != 'AlreadyExists':
                raise

    @staticmethod
    def _create_application_spec(deployment_config, image):
        # TODO basic config for deploy-daemon
        return FiaasApplicationSpec(application=deployment_config.name, image=image, config=default_config)
