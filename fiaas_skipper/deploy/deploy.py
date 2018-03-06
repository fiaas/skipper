#!/usr/bin/env python
# -*- coding: utf-8
import logging
import pinject

from k8s.client import NotFound
from k8s.models.common import ObjectMeta
from k8s.models.configmap import ConfigMap
from k8s.models.deployment import Deployment
from k8s.models.job import Job, JobSpec
from k8s.models.pod import Container, PodSpec, PodTemplateSpec

LOG = logging.getLogger(__name__)
NAME = 'fiaas-deploy-daemon'


class Deployer(object):
    @pinject.copy_args_to_internal_fields
    def __init__(self, cluster, release_channel_factory):
        pass

    def deploy(self):
        deployment_configs = self._cluster.find_deployment_configs(NAME)
        for deployment_config in deployment_configs:
            channel = self._release_channel_factory(deployment_config.name, deployment_config.tag)
            self._deploy(deployment_config, channel)
            if self._requires_bootstrap(deployment_config):
                self._bootstrap(deployment_config)

    def _deploy(self):
        raise NotImplementedError("Subclass must override _deploy")

    def _bootstrap(self, deployment_config):
        LOG.info("Bootstrapping %s in %s", deployment_config.name, deployment_config.namespace)
        # TODO create and run k8s job for fdd in bootstrap mode
        # The following is just a template for running a particular job until completion on kubernetes
        # Based on the kubernetes api documentation the sample job calculates pi with x number of decimals
        labels = {"test": "true"}
        object_meta = ObjectMeta(generateName="calc-pi-", namespace=deployment_config.namespace, labels=labels)
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
    def _requires_bootstrap(deployment_config):
        try:
            Deployment.get(name=deployment_config.name, namespace=deployment_config.namespace)
            return False
        except NotFound:
            return True
        except Exception as e:
            LOG.warn(e, exc_info=True)

    @staticmethod
    def _create_metadata(deployment_config):
        return ObjectMeta(name=deployment_config.name, namespace=deployment_config.namespace, labels={"fiaas/bootstrap": "true"})


class DeploymentConfig(object):
    @pinject.copy_args_to_public_fields
    def __init__(self, name, namespace, tag):
        pass


class DeploymentConfigStatus(object):
    @pinject.copy_args_to_public_fields
    def __init__(self, name, namespace, status, description):
        pass


class Cluster(object):
    @staticmethod
    def find_deployment_configs(name):
        res = []
        configmaps = [c for c in ConfigMap.list() if c.metadata.name == name]
        for c in configmaps:
            tag = c.data['tag'] if 'tag' in c.data else 'stable'
            res.append(DeploymentConfig(name=NAME, namespace=c.metadata.namespace, tag=tag))
        return res

    @staticmethod
    def find_deployment_config_statuses(name):
        res = []
        configmaps = [c for c in ConfigMap.list() if c.metadata.name == name]
        LOG.info(configmaps)
        for c in configmaps:
            description = None
            try:
                dep = Deployment.get(name=name, namespace=c.metadata.namespace)
                if dep.status.availableReplicas >= dep.spec.replicas:
                    status = 'SUCCESS'
                else:
                    status = 'FAILED'
                    description = 'Available replicas does not match the number of replicas in spec'
            except NotFound:
                status = 'NOT FOUND'
                description = 'No deployment found for given namespace - needs bootstrapping'
            except Exception as e:
                LOG.warn(e, exc_info=True)
                status = 'ERROR'
                description = e.message
            res.append(DeploymentConfigStatus(name=name, namespace=c.metadata.namespace, status=status, description=description))
        return res
