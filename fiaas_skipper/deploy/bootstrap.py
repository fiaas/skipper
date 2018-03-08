import logging

from k8s.client import NotFound
from k8s.models.common import ObjectMeta
from k8s.models.deployment import Deployment
from k8s.models.job import JobSpec, Job
from k8s.models.pod import Container, PodSpec, PodTemplateSpec

LOG = logging.getLogger(__name__)


def bootstrap(deployment_config, channel):
    LOG.info("Bootstrapping %s in %s", deployment_config.name, deployment_config.namespace)
    labels = {"test": "true"} # Perhaps we can use this label to track the bootstrap jobs
    object_meta = ObjectMeta(generateName="bootstrap-fiaas-",
                             namespace=deployment_config.namespace,
                             labels=labels)
    container = Container(
        name="fiaas-deploy-daemon-bootstrap",
        image=channel.metadata['image'],
        command=["fiaas-deploy-daemon-bootstrap"]
    )
    pod_spec = PodSpec(containers=[container], serviceAccountName="default", restartPolicy="Never")
    pod_template_spec = PodTemplateSpec(metadata=ObjectMeta(name="fiaas-deploy-daemon-bootstrap"), spec=pod_spec)
    job_spec = JobSpec(template=pod_template_spec)
    job = Job(metadata=object_meta, spec=job_spec)
    job.save()


def requires_bootstrap(deployment_config):
    try:
        Deployment.get(name=deployment_config.name, namespace=deployment_config.namespace)
        return False
    except NotFound:
        return True
    except Exception as e:
        LOG.warn(e, exc_info=True)
