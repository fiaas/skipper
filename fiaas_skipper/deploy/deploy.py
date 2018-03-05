#!/usr/bin/env python
# -*- coding: utf-8
import logging
import pinject

from k8s.client import NotFound
from k8s.models.common import ObjectMeta
from k8s.models.job import Job, JobSpec
from k8s.models.pod import Container, PodSpec, PodTemplateSpec

LOG = logging.getLogger(__name__)
NAME = 'fiaas-deploy-daemon'


class Deployer(object):
    @pinject.copy_args_to_internal_fields
    def __init__(self, cluster, release_channel_factory, k8s):
        pass

    def deploy(self):
        deployments = self.cluster.find_deployments(NAME)
        for deployment in deployments:
            channel = self.release_channel_factory(deployment.name, deployment.tag)
            self._deploy(deployment, channel)
            if deployment.bootstrap():
                self._bootstrap(deployment)

    def _deploy(self):
        raise NotImplementedError("Subclass must override _deploy")

    def _bootstrap(self, deployment):
        LOG.info("Bootstrapping %s in %s", deployment.name, deployment.namespace)
        # TODO create and run k8s job for fdd in bootstrap mode
        # The following is just a template for running a particular job until completion on kubernetes
        # Based on the kubernetes api documentation the sample job calculates pi with x number of decimals
        labels = {"test": "true"}
        object_meta = ObjectMeta(generateName="calc-pi-", namespace=deployment.namespace, labels=labels)
        container = Container(
            name="pi",
            image="perl",
            command=["perl", "-Mbignum=bpi", "-wle", "print bpi(2000)"]
        )
        pod_spec = PodSpec(containers=[container], serviceAccountName="default", restartPolicy="Never")
        pod_template_spec = PodTemplateSpec(metadata=ObjectMeta(name="calc-pi"), spec=pod_spec)
        job_spec = JobSpec(template=pod_template_spec)
        job = Job(metadata=object_meta, spec=job_spec)
        job.save()


    @staticmethod
    def _create_metadata(deployment):
        return ObjectMeta(name=deployment.name, namespace=deployment.namespace, labels={"fiaas/bootstrap": "true"})


class Deployment(object):
    @pinject.copy_args_to_internal_fields
    def __init__(self, name, namespace, tag, status):
        pass

    def bootstrap(self):
        return self.status == DeploymentStatus.NOTFOUND


class DeploymentStatus(object):
    OK = 'ok'
    UNAVAILABLE = 'unavailable'
    NOTFOUND = 'notfound'
    ERROR = 'error'


class Cluster(object):
    @pinject.copy_args_to_internal_fields
    def __init__(self, k8s):
        pass

    def find_deployments(self, name):
        res = []
        configmaps = self.k8s.configmaps()
        for c in configmaps:
            if c.metadata.name == name:
                tag = c.data['tag'] if 'tag' in c.data else 'stable'
                status = self._get_status(name=name, namespace=c.metadata.namespace)
                res.append(Deployment(name=NAME, namespace=c.metadata.namespace, tag=tag, status=status))
        return res

    def _get_status(self, **kwargs):
        try:
            dep = self.k8s.deployments(**kwargs)
            status = DeploymentStatus.OK if dep and dep.status.availableReplicas >= dep.spec.replicas else DeploymentStatus.UNAVAILABLE
        except NotFound:
            status = DeploymentStatus.NOTFOUND
        except Exception as e:
            LOG.warn(e, exc_info=True)
            status = DeploymentStatus.ERROR
        return status
