#!/usr/bin/env python
# -*- coding: utf-8
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
    def __init__(self, cmd_args=[]):
        self._cmd_args = cmd_args

    def __call__(self, deployment_config, channel, spec_config=None):
        namespace = deployment_config.namespace
        bootstrap_counter.inc()
        LOG.info("Bootstrapping %s in %s", deployment_config.name, namespace)
        try:
            Pod.delete(name=BOOTSTRAP_POD_NAME, namespace=namespace)
        except NotFound:
            pass
        pod_spec = _create_pod_spec(self._cmd_args, channel, namespace, spec_config)
        pod_metadata = _create_pod_metadata(namespace, spec_config)
        pod = Pod(metadata=pod_metadata, spec=pod_spec)
        pod.save()


def _create_pod_spec(args, channel, namespace, spec_config):
    container = Container(
        name="fiaas-deploy-daemon-bootstrap",
        image=channel.metadata['image'],
        command=["fiaas-deploy-daemon-bootstrap"] + args,
        resources=_create_resource_requirements(namespace, spec_config)
    )
    pod_spec = PodSpec(containers=[container], serviceAccountName="default", restartPolicy="Never")
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
