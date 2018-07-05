#!/usr/bin/env python
# -*- coding: utf-8

import pytest
from k8s.models.common import ObjectMeta
from k8s.models.configmap import ConfigMap
from k8s.models.deployment import Deployment, DeploymentStatus, DeploymentSpec
from k8s.models.pod import PodTemplateSpec, PodSpec, Container
from mock import mock

from fiaas_skipper.deploy.cluster import Cluster

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


def _assert_deployment_config(result, namespace, tag):
    assert namespace == result.namespace
    assert tag == result.tag


def _assert_deployment_config_status(deployment_config_status, namespace, status):
    assert namespace == deployment_config_status.namespace
    assert status == deployment_config_status.status


class TestCluster(object):
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

    @pytest.mark.usefixtures("config_map_find")
    def test_finds_deployment_configs(self):
        cluster = Cluster()
        results = cluster.find_deployment_configs(NAME)

        assert len(results) == 5
        _assert_deployment_config(results[0], "ns1", "stable")
        _assert_deployment_config(results[1], "ns2", "latest")
        _assert_deployment_config(results[2], "ns3", "stable")

    @pytest.mark.usefixtures("config_map_find")
    def test_finds_deployment_config_status(self, deployment_find):
        deployment_find.return_value = (
            _create_deployment(1, "ns1", "image:stable"),
            _create_deployment(0, "ns2", "image:latest"),
            _create_deployment(None, "ns4", "image:stable"),
        )

        cluster = Cluster()
        results = cluster.find_deployment_config_statuses(NAME)

        assert len(results) == 5
        _assert_deployment_config_status(results[0], "ns1", "SUCCESS")
        _assert_deployment_config_status(results[1], "ns2", "FAILED")
        _assert_deployment_config_status(results[2], "ns3", "NOT FOUND")
        _assert_deployment_config_status(results[3], "ns4", "UNAVAILABLE")
        _assert_deployment_config_status(results[4], "ns5", "NOT FOUND")
