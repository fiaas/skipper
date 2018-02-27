import pinject

from .channel import ReleaseChannelFactory
from .deploy import FiaasDeployDaemonDeployer, Cluster


class DeployBindings(pinject.BindingSpec):
    def configure(self, bind):
        bind("cluster", to_class=Cluster)
        bind("release_channel_factory", to_class=ReleaseChannelFactory)
        bind("deployer", to_class=FiaasDeployDaemonDeployer)
