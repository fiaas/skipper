#!/usr/bin/env python
# -*- coding: utf-8
import pytest
from mock import mock

from fiaas_skipper.update import AutoUpdater
from fiaas_skipper.deploy.channel import ReleaseChannel
from fiaas_skipper.deploy.deploy import DeploymentStatus, Deployer, StatusTracker


def _create_deployment_status(namespace, status='OK', version='123'):
    return DeploymentStatus(name='fiaas-deploy-daemon',
                            namespace=namespace,
                            description=None,
                            version=version,
                            status=status,
                            channel='stable')


class TestAutoUpdater(object):
    @pytest.fixture
    def deployer(self):
        return mock.create_autospec(Deployer)

    @pytest.fixture
    def status(self):
        return mock.create_autospec(StatusTracker, instance=True)

    @pytest.fixture
    def release_channel_factory(self):
        with mock.MagicMock(name="release_channel_factory") as factory:
            yield factory

    def test_check_updates_deploys_new_version(self, release_channel_factory, deployer, status):
        status.return_value = [
            _create_deployment_status(namespace='test1', version='111'),
            _create_deployment_status(namespace='test2', version='111'),
            _create_deployment_status(namespace='test2', version='123'),
            _create_deployment_status(namespace='test2', version='123'),
        ]
        release_channel_factory.side_effect = (
            lambda name, tag: ReleaseChannel(name=name, tag=tag, metadata={'image': 'image:new'}, spec={}))
        updater = AutoUpdater(release_channel_factory=release_channel_factory, deployer=deployer, status=status)
        updater.check_updates()
        deployer.deploy.assert_called_once_with(namespaces={'test1', 'test2'})

    def test_no_updates_no_deployment(self, release_channel_factory, deployer, status):
        status.return_value = [
            _create_deployment_status(namespace='test1'),
            _create_deployment_status(namespace='test2')
        ]
        release_channel_factory.side_effect = (
            lambda name, tag: ReleaseChannel(name=name, tag=tag, metadata={'image': 'image:123'}, spec={}))
        updater = AutoUpdater(release_channel_factory=release_channel_factory, deployer=deployer, status=status)
        updater.check_updates()
        deployer.deploy.assert_not_called()

    def test_check_bootstrap_deploys_new_version(self, release_channel_factory, deployer, status):
        status.return_value = [
            _create_deployment_status(namespace='test1', status='NOT_FOUND')
        ]
        updater = AutoUpdater(release_channel_factory=release_channel_factory, deployer=deployer, status=status)
        updater.check_bootstrap()
        deployer.deploy.assert_called_once_with(namespaces=['test1'])
