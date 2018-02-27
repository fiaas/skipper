import logging

from k8s.client import NotFound
from k8s.models.common import ObjectMeta

from fiaas_skipper.tpr.types import PaasbetaApplicationSpec, PaasbetaApplication
from ..crd.types import FiaasApplication, FiaasApplicationSpec

LOG = logging.getLogger(__name__)
NAME = 'fiaas-deploy-daemon'


class FiaasDeployDaemonDeployer(object):
    def __init__(self, cluster, release_channel_factory, k8s, config):
        self.cluster = cluster
        self.release_channel_factory = release_channel_factory
        self.k8s = k8s
        self.config = config

    def deploy(self):
        deployments = self.cluster.find_deployments(NAME)
        for deployment in deployments:
            self._deploy(deployment)

    def _deploy(self, deployment):
        LOG.info("Deploying %s to %s", NAME, deployment.namespace)
        channel = self.release_channel_factory(NAME, deployment.tag)
        if self.config.enable_crd_support:
            fdd_app = FiaasApplication(metadata=_create_metadata(namespace=deployment.namespace),
                                       spec=_create_application_spec(image=channel.image))
            fdd_app.save()
        elif self.config.enable_tpr_support:
            pba = PaasbetaApplication(metadata=_create_metadata(namespace=deployment.namespace),
                                      spec=_create_paasbetaapplicationspec())
            pba.save()
        if deployment.status == DeploymentStatus.NOTFOUND:
            self._bootstrap(deployment.namespace)

    def _bootstrap(self, namespace):
        LOG.info("Bootstrapping %s in %s", NAME, namespace)
        # TODO create and run k8s job


def _create_metadata(namespace):
    return ObjectMeta(name=NAME, namespace=namespace, labels={"fiaas/bootstrap": "true"})


def _create_application_spec(image):
    return FiaasApplicationSpec(application=NAME, image=image, config={})


def _create_paasbetaapplicationspec(image):
    return PaasbetaApplicationSpec(application=NAME, image=image, config={})


class Deployment(object):
    def __init__(self, namespace, tag, status):
        self.namespace = namespace
        self.tag = tag
        self.status = status


class DeploymentStatus(object):
    OK = 'ok'
    UNAVAILABLE = 'unavailable'
    NOTFOUND = 'notfound'
    ERROR = 'error'


class Cluster(object):
    def __init__(self, k8s):
        self.k8s = k8s

    def find_deployments(self, module_name):
        res = []
        configmaps = self.k8s.configmaps()
        for c in configmaps:
            if c.metadata.name == module_name:
                tag = c.data['tag'] if 'tag' in c.data else 'stable'
                try:
                    dep = self.k8s.deployments(name=module_name, namespace=c.metadata.namespace)
                    status = DeploymentStatus.OK if dep and dep.status.availableReplicas >= dep.spec.replicas else DeploymentStatus.UNAVAILABLE
                except NotFound:
                    status = DeploymentStatus.NOTFOUND
                except Exception as e:
                    LOG.warn(e, exc_info=True)
                    status = DeploymentStatus.ERROR
                res.append(Deployment(namespace=c.metadata.namespace, tag=tag, status=status))
        return res
