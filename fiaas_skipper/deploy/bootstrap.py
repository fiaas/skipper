#!/usr/bin/env python
# -*- coding: utf-8

# Copyright 2017-2019 The FIAAS Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import logging

from k8s.client import NotFound
from k8s.models.common import ObjectMeta
from k8s.models.pod import Container, PodSpec, Pod, ResourceRequirements
from k8s.models.resourcequota import ResourceQuota, NotBestEffort
from prometheus_client import Counter

BOOTSTRAP_POD_NAME = "fiaas-deploy-daemon-bootstrap"

LOG = logging.getLogger(__name__)

bootstrap_counter = Counter("bootstraps_triggered", "A deployment caused a bootstrap to be triggered")


class BarePodBootstrapper(object):
    def __init__(self, cmd_args=None):
        self._cmd_args = [] if cmd_args is None else cmd_args

    def __call__(self, deployment_config, channel, spec_config=None, rbac=False):
        namespace = deployment_config.namespace
        bootstrap_counter.inc()
        LOG.info("Bootstrapping %s in %s", deployment_config.name, namespace)
        try:
            Pod.delete(name=BOOTSTRAP_POD_NAME, namespace=namespace)
        except NotFound:
            pass
        args = self._cmd_args
        if deployment_config.service_account_per_app:
            args.append("--enable-service-account-per-app")
        pod_spec = _create_pod_spec(args, channel, namespace, spec_config, rbac=rbac)
        pod_metadata = _create_pod_metadata(namespace, spec_config)
        pod = Pod(metadata=pod_metadata, spec=pod_spec)
        pod.save()


def _create_pod_spec(args, channel, namespace, spec_config, rbac=False):
    container = Container(
        name="fiaas-deploy-daemon-bootstrap",
        image=channel.metadata['image'],
        command=["fiaas-deploy-daemon-bootstrap"] + args,
        resources=_create_resource_requirements(namespace, spec_config)
    )
    pod_spec = PodSpec(containers=[container], serviceAccountName="default", restartPolicy="Never")
    if rbac:
        pod_spec.serviceAccountName = "fiaas-deploy-daemon"
    return pod_spec


def _create_pod_metadata(namespace, spec_config):
    pod_annotations = _get_pod_annotations(spec_config)
    pod_metadata = ObjectMeta(name=BOOTSTRAP_POD_NAME,
                              annotations=pod_annotations,
                              labels={"app": BOOTSTRAP_POD_NAME},
                              namespace=namespace)
    return pod_metadata


def _get_pod_annotations(spec_config):
    if spec_config:
        try:
            return spec_config["annotations"]["pod"]
        except KeyError:
            pass
    return {}


def _create_resource_requirements(namespace, spec_config):
    if not spec_config or _only_besteffort_qos_is_allowed(namespace):
        return ResourceRequirements()
    else:
        return ResourceRequirements(limits=spec_config.get('resources', {}).get('limits', None),
                                    requests=spec_config.get('resources', {}).get('requests', None))


def _only_besteffort_qos_is_allowed(namespace):
    resourcequotas = ResourceQuota.list(namespace=namespace)
    return any(rq.spec.hard.get("pods") == "0" and NotBestEffort in rq.spec.scopes for rq in resourcequotas)
