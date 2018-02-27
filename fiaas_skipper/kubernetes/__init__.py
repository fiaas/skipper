import pinject

from .adapter import K8s


class KubernetesBindings(pinject.BindingSpec):
    def configure(self, bind):
        bind("k8s", to_class=K8s)
