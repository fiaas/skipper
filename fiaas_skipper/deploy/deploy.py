import logging

from k8s.client import NotFound
from k8s.models.common import ObjectMeta

LOG = logging.getLogger(__name__)
NAME = 'fiaas-deploy-daemon'


class Deployer(object):
    def __init__(self, cluster, release_channel_factory, k8s):
        self.cluster = cluster
        self.release_channel_factory = release_channel_factory
        self.k8s = k8s

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
        # TODO create and run k8s job

    @staticmethod
    def _create_metadata(deployment):
        return ObjectMeta(name=deployment.name, namespace=deployment.namespace, labels={"fiaas/bootstrap": "true"})


class Deployment(object):
    def __init__(self, namespace, tag, status):
        self.name = NAME
        self.namespace = namespace
        self.tag = tag
        self.status = status

    def bootstrap(self):
        return self.status == DeploymentStatus.NOTFOUND


class DeploymentStatus(object):
    OK = 'ok'
    UNAVAILABLE = 'unavailable'
    NOTFOUND = 'notfound'
    ERROR = 'error'


class Cluster(object):
    def __init__(self, k8s):
        self.k8s = k8s

    def find_deployments(self, name):
        res = []
        configmaps = self.k8s.configmaps()
        for c in configmaps:
            if c.metadata.name == name:
                tag = c.data['tag'] if 'tag' in c.data else 'stable'
                status = self._get_status(name=name, namespace=c.metadata.namespace)
                res.append(Deployment(namespace=c.metadata.namespace, tag=tag, status=status))
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
