#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import pkg_resources
import yaml

_resource_stream = pkg_resources.resource_stream(__name__, "fiaas.yml")
default_config = yaml.load(_resource_stream)

from .deploy import Cluster, DeploymentConfigStatus, DeploymentConfig
from .channel import ReleaseChannelFactory, ReleaseChannel

from .tpr import TprDeployer, TprBootstrapper
from .crd import CrdDeployer, CrdBootstrapper
