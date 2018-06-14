from __future__ import absolute_import

import copy

import pytest

from fiaas_skipper.deploy.deploy import DeploymentConfig, default_spec_config
from fiaas_skipper.deploy.channel import ReleaseChannel
from fiaas_skipper.deploy.bootstrap import BarePodBootstrapper


class TestBarePodBootstrapper():

    def pod_uri(self, namespace="default", name=""):
        return f'/api/v1/namespaces/{namespace}/pods/{name}'

    @pytest.fixture
    def spec_config(self):
        return copy.deepcopy(default_spec_config)

    @pytest.mark.parametrize("namespace,resourcequotas,resources", [
        ("default", [], {
            'requests': {
                'memory': '256Mi',
            },
        }),
    ])
    def test_bootstrap(self, post, delete, namespace, resourcequotas, resources, spec_config):
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
                    'resources': resources,
                }],
                'restartPolicy': 'Never',
                'dnsPolicy': 'ClusterFirst',
                'serviceAccountName': 'default',
                'imagePullSecrets': [],
                'initContainers': [],
            }
        }

        bootstrapper(deployment_config, channel, spec_config=spec_config)

        pytest.helpers.assert_any_call(delete, self.pod_uri(namespace=namespace, name='fiaas-deploy-daemon-bootstrap'))
        pytest.helpers.assert_any_call(post, self.pod_uri(namespace=namespace), expected_pod)
