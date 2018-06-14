from __future__ import absolute_import

import copy
import mock

from k8s.models.resourcequota import ResourceQuota, ResourceQuotaSpec,  NotBestEffort, BestEffort
from k8s.models.common import ObjectMeta
import pytest

from fiaas_skipper.deploy.deploy import DeploymentConfig, default_spec_config
from fiaas_skipper.deploy.channel import ReleaseChannel
from fiaas_skipper.deploy.bootstrap import BarePodBootstrapper


ONLY_BEST_EFFORT_ALLOWED = {
    "hard": {
        "pods": "0",
    },
    "scopes": [NotBestEffort],
}

BEST_EFFORT_NOT_ALLOWED = {
    "hard": {
        "pods": "0",
    },
    "scopes": [BestEffort],
}

def spec_config(resources=None):
    config = copy.deepcopy(default_spec_config)
    if resources:
        config['resources'] = resources
    return config


class TestBarePodBootstrapper():

    def pod_uri(self, namespace="default", name=""):
        return f'/api/v1/namespaces/{namespace}/pods/{name}'

    @pytest.fixture
    def resourcequota_list(self):
        with mock.patch("k8s.models.resourcequota.ResourceQuota.list") as mockk:
            yield mockk

    def create_resourcequota(self, namespace, resourcequota_spec):
        metadata = ObjectMeta(name="foo", namespace=namespace)
        spec = ResourceQuotaSpec.from_dict(resourcequota_spec)
        return ResourceQuota(metadata=metadata, spec=spec)

    @pytest.mark.parametrize("namespace,resourcequota_spec,resources,spec_config", [
        ("default", None, spec_config()['resources'], spec_config()),
        ("other-namespace", None, spec_config()['resources'], spec_config()),
        ("other-namespace", None, spec_config()['resources'], spec_config()),
        ("default", ONLY_BEST_EFFORT_ALLOWED, None, spec_config()),
        ("other-namespace", ONLY_BEST_EFFORT_ALLOWED, None, spec_config()),
        ("default", BEST_EFFORT_NOT_ALLOWED, spec_config()['resources'], spec_config()),
        ("other-namespace", BEST_EFFORT_NOT_ALLOWED, spec_config()['resources'], spec_config()),
    ])
    def test_bootstrap(self, post, delete, resourcequota_list, namespace, resourcequota_spec, resources, spec_config):
        resourcequota_list.return_value = \
            [self.create_resourcequota(namespace, resourcequota_spec)] if resourcequota_spec else []
        bootstrapper = BarePodBootstrapper()
        channel = ReleaseChannel(None, None, {'image': 'example.com/image:tag'})
        deployment_config = DeploymentConfig('foo', namespace, 'latest')
        expected_pod = {
            'metadata': {
                'name': 'fiaas-deploy-daemon-bootstrap',
                'namespace': namespace,
                'labels': {'app': 'fiaas-deploy-daemon-bootstrap'},
                'ownerReferences': []
            },
            'spec': {
                'volumes': [],
                'containers': [{
                    'name': 'fiaas-deploy-daemon-bootstrap',
                    'image': 'example.com/image:tag',
                    'ports': [],
                    'env': [],
                    'envFrom': [],
                    'volumeMounts': [],
                    'imagePullPolicy': 'IfNotPresent',
                    'command': ['fiaas-deploy-daemon-bootstrap'],
                }],
                'restartPolicy': 'Never',
                'dnsPolicy': 'ClusterFirst',
                'serviceAccountName': 'default',
                'imagePullSecrets': [],
                'initContainers': [],
            }
        }
        if resources:
            expected_pod['spec']['containers'][0]['resources'] = resources

        bootstrapper(deployment_config, channel, spec_config=spec_config)

        pytest.helpers.assert_any_call(delete, self.pod_uri(namespace=namespace, name='fiaas-deploy-daemon-bootstrap'))
        pytest.helpers.assert_any_call(post, self.pod_uri(namespace=namespace), expected_pod)
