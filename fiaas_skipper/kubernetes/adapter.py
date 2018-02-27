from k8s.models.configmap import ConfigMap
from k8s.models.deployment import Deployment


class K8s(object):
    def configmaps(self):
        return ConfigMap.list()

    def deployments(self, **kwargs):
        return Deployment.get(kwargs)
