#!/usr/bin/env python
# -*- coding: utf-8
import mock
import pytest
from k8s.models.common import ObjectMeta
from k8s.models.configmap import ConfigMap
from k8s.models.deployment import DeploymentSpec, Deployment, DeploymentStatus
from k8s.models.pod import Container, PodSpec, PodTemplateSpec

from fiaas_skipper.deploy.channel import ReleaseChannel
from fiaas_skipper.deploy.cluster import DeploymentConfig
from fiaas_skipper.deploy.crd.types import FiaasApplicationSpec, FiaasApplication
from fiaas_skipper.deploy.deploy import Deployer

NAME = "deployment_target"


def _create_configmap(namespace, tag=None):
    metadata = ObjectMeta(name=NAME, namespace=namespace)
    data = {}
    if tag:
        data["tag"] = tag
    return ConfigMap(metadata=metadata, data=data)


def _create_deployment(available_replicas, namespace, image):
    container = Container(image=image)
    pod_spec = PodSpec(containers=[container])
    pod_template_spec = PodTemplateSpec(spec=pod_spec)
    spec = DeploymentSpec(replicas=1, template=pod_template_spec)
    status = DeploymentStatus(availableReplicas=available_replicas)
    metadata = ObjectMeta(name=NAME, namespace=namespace)
    return Deployment(metadata=metadata, spec=spec, status=status)


def _create_application(namespace, image):
    spec = FiaasApplicationSpec(application='fdd', image=image, config={})
    metadata = ObjectMeta(name='fdd', namespace=namespace)
    return FiaasApplication(metadata=metadata, spec=spec)


def _assert_deployment_config_status(deployment_config_status, namespace, status):
    assert namespace == deployment_config_status.namespace
    assert status == deployment_config_status.status


class TestDeployer(object):
    @pytest.fixture
    def cluster(self):
        cluster = mock.NonCallableMagicMock(name="cluster")
        cluster.find_deployment_configs.return_value = (
            DeploymentConfig("test1", "test1", "stable"),
            DeploymentConfig("test2", "test2", "stable"),
        )
        return cluster

    @pytest.fixture
    def release_channel_factory(self):
        channel_factory = mock.MagicMock(name="release_channel_factory")
        channel_factory.return_value = ReleaseChannel(
            name="xx",
            tag="stable",
            metadata={"image": "image1",
                      "spec": "http://example.com/fiaas.yml"},
            spec="version: 3",
        )
        return channel_factory

    @pytest.fixture
    def config_map_find(self):
        with mock.patch("k8s.models.configmap.ConfigMap.find") as finder:
            finder.return_value = (
                _create_configmap("ns1", "stable"),
                _create_configmap("ns2", "latest"),
                _create_configmap("ns3"),
                _create_configmap("ns4", "latest"),
                _create_configmap("ns5", "stable"),
            )
            yield finder

    @pytest.fixture
    def deployment_find(self):
        with mock.patch("k8s.models.deployment.Deployment.find") as finder:
            yield finder

    @pytest.fixture
    def application_find(self):
        with mock.patch('fiaas_skipper.deploy.deploy.Deployer._applications') as finder:
            yield finder

    def test_deploys_only_to_configured_namespaces(self, cluster, release_channel_factory):
        deployer = Deployer(cluster, release_channel_factory, None, deploy_interval=0)
        deployer._deploy = mock.MagicMock(name="_deploy")
        deployer.deploy(namespaces=("test1",))
        deployer._deploy.assert_called_once()

    def test_deploys_to_all_namespaces(self, cluster, release_channel_factory):
        deployer = Deployer(cluster, release_channel_factory, None, deploy_interval=0)
        deployer._deploy = mock.MagicMock(name="_deploy")
        deployer.deploy()
        assert 2 == deployer._deploy.call_count

    @pytest.mark.usefixtures("config_map_find")
    def test_deployment_statuses(self, cluster, release_channel_factory, deployment_find, application_find):
        deployment_find.return_value = (
            _create_deployment(1, "ns1", "image:stable"),
            _create_deployment(0, "ns2", "image:latest"),
            _create_deployment(None, "ns4", "image:stable"),
            _create_deployment(1, "ns5", "image:experimental"),
        )

        application_find.return_value = (
            _create_application("ns1", "image:stable"),
            _create_application("ns2", "image:latest"),
            _create_application("ns3", "image:latest"),
            _create_application("ns4", "image:stable"),
            _create_application("ns5", "image:stable"),
        )

        deployer = Deployer(cluster, release_channel_factory, None, deploy_interval=0)
        results = deployer.status()

        assert len(results) == 5
        _assert_deployment_config_status(results[0], "ns1", "OK")
        _assert_deployment_config_status(results[1], "ns2", "FAILED")
        _assert_deployment_config_status(results[2], "ns3", "NOT_FOUND")
        _assert_deployment_config_status(results[3], "ns4", "UNAVAILABLE")
        _assert_deployment_config_status(results[4], "ns5", "VERSION_MISMATCH")
