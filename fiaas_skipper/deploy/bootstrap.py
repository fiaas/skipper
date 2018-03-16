#!/usr/bin/env python
# -*- coding: utf-8
from __future__ import absolute_import

import logging

from k8s.models.common import ObjectMeta
from k8s.models.job import JobSpec, Job
from k8s.models.pod import Container, PodSpec, PodTemplateSpec
from prometheus_client import Counter

LOG = logging.getLogger(__name__)

bootstrap_counter = Counter("bootstraps_triggered", "A deployment caused a bootstrap to be triggered")


class Bootstrapper(object):
    def __init__(self, cmd_args=()):
        self._cmd_args = cmd_args

    def __call__(self, deployment_config, channel):
        bootstrap_counter.inc()
        LOG.info("Bootstrapping %s in %s", deployment_config.name, deployment_config.namespace)
        labels = {"test": "true"}  # Perhaps we can use this label to track the bootstrap jobs
        object_meta = ObjectMeta(generateName="bootstrap-fiaas-",
                                 namespace=deployment_config.namespace,
                                 labels=labels)
        container = Container(
            name="fiaas-deploy-daemon-bootstrap",
            image=channel.metadata['image'],
            command=["fiaas-deploy-daemon-bootstrap"] + self._cmd_args
        )
        pod_spec = PodSpec(containers=[container], serviceAccountName="default", restartPolicy="Never")
        pod_template_spec = PodTemplateSpec(metadata=ObjectMeta(name="fiaas-deploy-daemon-bootstrap"), spec=pod_spec)
        job_spec = JobSpec(template=pod_template_spec)
        job = Job(metadata=object_meta, spec=job_spec)
        job.save()
