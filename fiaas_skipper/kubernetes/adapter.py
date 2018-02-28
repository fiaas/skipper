from k8s.models.configmap import ConfigMap
from k8s.models.deployment import Deployment


class K8s(object):
    @staticmethod
    def configmaps():
        return ConfigMap.list()

    @staticmethod
    def deployments(**kwargs):
        return Deployment.get(kwargs)
