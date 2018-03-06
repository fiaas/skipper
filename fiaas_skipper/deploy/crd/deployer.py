#!/usr/bin/env python
# -*- coding: utf-8
import logging

from k8s.client import ClientError

from .types import FiaasApplicationSpec, FiaasApplication
from ..deploy import Deployer

LOG = logging.getLogger(__name__)


class CrdDeployer(Deployer):
    def _deploy(self, deployment, channel):
        LOG.info("Deploying %s to %s", deployment.name, deployment.namespace)
        try:
            fdd_app = FiaasApplication(metadata=self._create_metadata(deployment=deployment),
                                       spec=self._create_application_spec(deployment, image=channel.metadata['image']))
            fdd_app.save()
        except ClientError as e:
            if e.response.json()['reason'] != 'AlreadyExists':
                raise

    @staticmethod
    def _create_application_spec(deployment, image):
        return FiaasApplicationSpec(application=deployment.name, image=image, config={})
