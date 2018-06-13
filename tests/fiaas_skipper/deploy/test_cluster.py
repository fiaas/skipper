#!/usr/bin/env python
# -*- coding: utf-8

import pytest
from k8s.client import NotFound
from k8s.models.common import ObjectMeta
from k8s.models.configmap import ConfigMap
from k8s.models.deployment import Deployment, DeploymentStatus, DeploymentSpec
from mock import mock

from fiaas_skipper.deploy.cluster import Cluster

NAME = "deployment_target"


def _create_configmap(namespace, tag=None):
    metadata = ObjectMeta(name=NAME, namespace=namespace)
    data = {}
    if tag:
        data["tag"] = tag
    return ConfigMap(metadata=metadata, data=data)


def _create_deployment(available_replicas=1):
    spec = DeploymentSpec(replicas=1)
    status = DeploymentStatus(availableReplicas=available_replicas)
    return Deployment(spec=spec, status=status)


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
    def deployment_get(self):
        with mock.patch("k8s.models.deployment.Deployment.get") as getter:
            yield getter

    @pytest.mark.usefixtures("config_map_find")
    def test_finds_deployment_configs(self):
        cluster = Cluster()
        results = cluster.find_deployment_configs(NAME)

        assert len(results) == 5
        _assert_deployment_config(results[0], "ns1", "stable")
        _assert_deployment_config(results[1], "ns2", "latest")
        _assert_deployment_config(results[2], "ns3", "stable")

    @pytest.mark.usefixtures("config_map_find")
    def test_finds_deployment_config_status(self, deployment_get):
        deployment_get.side_effect = (
            _create_deployment(),
            _create_deployment(0),
            NotFound,
            TypeError,
            Exception("error"),
        )

        cluster = Cluster()
        results = cluster.find_deployment_config_statuses(NAME)

        assert len(results) == 5
        _assert_deployment_config_status(results[0], "ns1", "SUCCESS")
        _assert_deployment_config_status(results[1], "ns2", "FAILED")
        _assert_deployment_config_status(results[2], "ns3", "NOT FOUND")
        _assert_deployment_config_status(results[3], "ns4", "UNAVAILABLE")
        _assert_deployment_config_status(results[4], "ns5", "ERROR")
