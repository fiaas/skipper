#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging
import random
import string

from k8s.models.common import ObjectMeta
from k8s.models.job import JobSpec, Job
from k8s.models.pod import Container, PodSpec, PodTemplateSpec, Pod
from prometheus_client import Counter

LOG = logging.getLogger(__name__)

bootstrap_counter = Counter("bootstraps_triggered", "A deployment caused a bootstrap to be triggered")


class BatchJobsBootstrapper(object):
    def __init__(self, cmd_args=()):
        self._cmd_args = cmd_args

    def __call__(self, deployment_config, channel, spec_config=None):
        bootstrap_counter.inc()
        LOG.info("Bootstrapping %s in %s", deployment_config.name, deployment_config.namespace)
        object_meta = ObjectMeta(generateName="bootstrap-fiaas-",
                                 namespace=deployment_config.namespace)
        container = Container(
            name="fiaas-deploy-daemon-bootstrap",
            image=channel.metadata['image'],
            command=["fiaas-deploy-daemon-bootstrap"] + self._cmd_args
        )
        pod_spec = PodSpec(containers=[container], serviceAccountName="default", restartPolicy="Never")
        pod_annotations = _get_pod_annotations(spec_config)
        pod_metadata = ObjectMeta(name="fiaas-deploy-daemon-bootstrap", annotations=pod_annotations)
        pod_template_spec = PodTemplateSpec(metadata=pod_metadata, spec=pod_spec)
        job_spec = JobSpec(template=pod_template_spec, backoffLimit=5)
        job = Job(metadata=object_meta, spec=job_spec)
        job.save()


class BarePodBootstrapper(object):
    def __init__(self, cmd_args=()):
        self._cmd_args = cmd_args

    def __call__(self, deployment_config, channel, spec_config=None):
        bootstrap_counter.inc()
        LOG.info("Bootstrapping %s in %s", deployment_config.name, deployment_config.namespace)
        container = Container(
            name="fiaas-deploy-daemon-bootstrap",
            image=channel.metadata['image'],
            command=["fiaas-deploy-daemon-bootstrap"] + self._cmd_args
        )
        pod_spec = PodSpec(containers=[container], serviceAccountName="default", restartPolicy="Never")
        pod_annotations = _get_pod_annotations(spec_config)
        pod_metadata = ObjectMeta(name="fiaas-deploy-daemon-bootstrap-" +
                                       ''.join(random.choices(string.ascii_lowercase, k=8)),
                                  annotations=pod_annotations,
                                  namespace=deployment_config.namespace)
        pod = Pod(metadata=pod_metadata, spec=pod_spec)
        pod.save()


def _get_pod_annotations(spec_config):
    if spec_config:
        try:
            return spec_config["annotations"]["pod"]
        except KeyError:
            pass
    return {}
