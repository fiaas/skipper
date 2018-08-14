#!/usr/bin/env python
# -*- coding: utf-8
import pytest
from mock import mock

from fiaas_skipper.update import AutoUpdater, TAGS
from fiaas_skipper.deploy.channel import ReleaseChannel
from fiaas_skipper.deploy.deploy import DeploymentStatus, Deployer


def _create_deployment_status(namespace, status):
    return DeploymentStatus(name='fiaas-deploy-daemon',
                            namespace=namespace,
                            description=None,
                            version=None,
                            status=status)


class TestAutoUpdater(object):
    @pytest.fixture
    def deployer(self):
        return mock.create_autospec(Deployer)

    @pytest.fixture
    def release_channel_factory(self):
        with mock.MagicMock(name="release_channel_factory") as factory:
            yield factory

    def test_check_updates_deploys_new_version(self, release_channel_factory, deployer):
        release_channel_factory.side_effect = (
            lambda name, tag: ReleaseChannel(name=name, tag=tag, metadata={'image': 'new'}, spec={}))
        updater = AutoUpdater(release_channel_factory=release_channel_factory, deployer=deployer)
        updater._images = dict((t, 'old') for t in TAGS)
        updater.check_updates()
        deployer.deploy.assert_called_once()
        assert updater._images == dict((t, 'new') for t in TAGS)

    def test_no_updates_no_deployment(self, release_channel_factory, deployer):
        release_channel_factory.side_effect = (
            lambda name, tag: ReleaseChannel(name=name, tag=tag, metadata={'image': 'old'}, spec={}))
        updater = AutoUpdater(release_channel_factory=release_channel_factory, deployer=deployer)
        updater._images = dict((t, 'old') for t in TAGS)
        updater.check_updates()
        deployer.deploy.assert_not_called()

    def test_check_bootstrap_deploys_new_version(self, release_channel_factory, deployer):
        deployer.status.return_value = [
            _create_deployment_status(namespace='test1', status='NOT_FOUND'),
            _create_deployment_status(namespace='test2', status='OK')
        ]
        updater = AutoUpdater(release_channel_factory=release_channel_factory, deployer=deployer)
        updater.check_bootstrap()
        deployer.deploy.assert_called_once_with(namespaces=['test1'])
