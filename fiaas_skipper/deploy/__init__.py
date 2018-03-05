#!/usr/bin/env python
# -*- coding: utf-8
import pinject

from .channel import ReleaseChannelFactory
from .deploy import Cluster


class DeployBindings(pinject.BindingSpec):
    def configure(self, bind, require):
        bind("cluster", to_class=Cluster)
        bind("release_channel_factory", to_class=ReleaseChannelFactory)
