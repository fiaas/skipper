<!--
Copyright 2017-2019 The FIAAS Authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
# SKIPPER [![build_status_badge]][build_status] [![codacy_grade_badge]][codacy_grade] [![codacy_coverage_badge]][codacy_coverage]

Skipper controls deployment and updates of FIAAS components

[build_status_badge]: https://travis-ci.org/fiaas/skipper.svg?branch=master "Build Status"
[build_status]: https://travis-ci.org/fiaas/skipper
[codacy_grade_badge]: https://api.codacy.com/project/badge/Grade/59dbd659e01f4e04ad724ae4c8abe2d5 "Codacy Grade"
[codacy_grade]: https://app.codacy.com/app/fiaas/skipper?utm_source=github.com&utm_medium=referral&utm_content=fiaas/skipper&utm_campaign=badger
[codacy_coverage_badge]: https://api.codacy.com/project/badge/Coverage/59dbd659e01f4e04ad724ae4c8abe2d5 "Codacy Coverage"
[codacy_coverage]: https://www.codacy.com/app/fiaas/skipper?utm_source=github.com&utm_medium=referral&utm_content=fiaas/skipper&utm_campaign=Badge_Coverage

## How skipper works

Skipper runs in your cluster, looking for namespaces configured for FIAAS. This is defined as having a ConfigMap named `fiaas-deploy-daemon` in the namespace. The ConfigMap supports two keys, one of which is required.

The required key is `cluster_config.yaml`, which configures fiaas-deploy-daemon. You should see the [FIAAS operators guide] for details about this file.

The second key is `tag`, which defaults to the value `stable` if left out. Currently the only other valid value is `latest`. This controls which version of fiaas-deploy-daemon to deploy to this namespace.

When triggered by a request to the `/api/deploy` endpoint, Skipper will list all configured namespaces, and create or update an Application object for fiaas-deploy-daemon in each namespace. This will point to the current `latest` or `stable` image, depending on the value of `tag`.

If no Deployment of fiaas-deploy-daemon exists in the namespace, a special "bare pod" is created, which runs fiaas-deploy-daemon in bootstrap mode. This pod will make a proper deployment of fiaas-deploy-daemon into the namespace, and then exit. The properly deployed fiaas-deploy-daemon will start by re-deploying itself, in order to do a final configuration load, and then start deploying applications in the namespace.

If there are many configured namespaces in the cluster, it might be useful to deploy only to a selected set of namespaces. This is possible by using the API, or the web UI of Skipper.

Skipper will detect when new versions of fiaas-deploy-daemon is available, and automatically update all configured namespaces with the new version. This enables a fully automatic continuous deploy solution for fiaas-deploy-daemon.

Skipper allows operators to force an update of fiaas-deploy-daemon in a given namespace.

### How skipper will work differently once currently planned features are completed

We are not done. We have planned some further features, which will improve the experience of using Skipper significantly. Here are some of the planned changes:

* Try to detect when an instance of fiaas-deploy-daemon is not operating properly, and re-deploy it

## Installation

With Helm:

```commandline
helm install --repo https://fiaas.github.io/helm fiaas-skipper --name fiaas-skipper
```

With Helm (including rbac):

```commandline
helm install --repo https://fiaas.github.io/helm fiaas-skipper --name fiaas-skipper --set rbac.enabled="true"
```

For more information on permissions required for fiaas-controller see [FIAAS operators guide].

Skipper will look for a fiaas-deploy-daemon configmap across namespaces in the cluster and will bootstrap and deploy a fiaas-deploy-daemon instance for any that are found. By default this configmap is not added when skipper is installed but the install command can be extended with `--set addFiaasDeployDaemonConfigmap="true"` to include the configmap which will make fiaas-skipper start an instance of the fiaas-deploy-daemon once installed. This is useful when bootstrapping fiaas for the first time in a new cluster.

## Deploying fiaas-deploy-daemon to a new namespace

Deploying fiaas-deploy-daemon to a new namespace can be done in a few simple steps, assuming you already have Skipper running in your cluster:

1. Create a FIAAS configuration in the namespace. See above, and [FIAAS operators guide] for details about how to do that.
2. Trigger a deploy to that namespace. This can be done in many ways:
    1. `POST` JSON similar to this to the `/api/deploy` endpoint:
        ```json
        {
            "namespaces": [
                "some-namespace",
                "other-namespace"
            ]
        }
        ```
    2. Use the Web UI at `/status`
    3. Or just `POST` to the `/api/deploy` endpoint with no data (this will trigger deploy to all configured namespaces, including yours).

## Troubleshooting

If you follow the above steps, but fiaas-deploy-daemon for some reason does not get deployed to your namespace, there are a few steps you can do to troubleshoot.

1. Check the Skipper logs for errors
2. If bootstrapping a new namespace, check the bootstrap pod logs:
    ```commandline
    kubectl logs -n some-namespace fiaas-deploy-daemon-bootstrap
    ```
3. If a Deployment exists, but no pods, check the Deployment for problems:
    ```commandline
    kubectl describe deploy -n some-namespace fiaas-deploy-daemon
    ```
4. If fiaas-deploy-daemon is deployed, but is not deploying any applications, check logs for fiaas-deploy-daemon:
    ```commandline
    kubectl logs -n some-namespace -lapp=fiaas-deploy-daemon
    ```
5. To force deployment it is possible to include a flag in the POST payload:
    1. `POST` JSON similar to this to the `/api/deploy` endpoint (including force bootstrap flag):
        ```json
        {
            "namespaces": [
                "some-namespace",
                "other-namespace"
            ],
            "force-bootstrap": true
        }
        ```
    2. Use the Web UI at `/status` and check `force bootstrap` in the deployment dialog when prompted


[FIAAS operators guide]: https://github.com/fiaas/fiaas-deploy-daemon/blob/master/docs/operator_guide.md

## Release Process

When changes are merged to master the master branch is built using [travis](https://travis-ci.org/fiaas/skipper). The build generates a docker image that is published to the [fiaas/skipper](https://cloud.docker.com/u/fiaas/repository/docker/fiaas/skipper) respository on docker hub and is publicly available.
Additionally a helm chart is created and published to the [fiaas helm repository](https://github.com/fiaas/helm).
