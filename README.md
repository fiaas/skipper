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
# SKIPPER [![https://fiaas-svc.semaphoreci.com/badges/skipper/branches/master.svg?style=shields]][https://fiaas-svc.semaphoreci.com/projects/skipper]

Skipper controls deployment and updates of FIAAS components
[build_status_badge]: "https://fiaas-svc.semaphoreci.com/badges/skipper/branches/master.svg?style=shields" "Build Status"
[build_status]: "https://fiaas-svc.semaphoreci.com/projects/skipper"
[codacy_grade_badge]: "https://app.codacy.com/project/badge/Grade/83b7598937694e1b92d706347d5124a3" "Codacy Grade"
[codacy_grade]: "https://www.codacy.com/gh/fiaas/skipper/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=fiaas/skipper&amp;utm_campaign=Badge_Grade"
[codacy_coverage_badge]: "https://app.codacy.com/project/badge/Coverage/83b7598937694e1b92d706347d5124a3" "Codacy Coverage"
[codacy_coverage]: "https://www.codacy.com/gh/fiaas/skipper/dashboard?utm_source=github.com&utm_medium=referral&utm_content=fiaas/skipper&utm_campaign=Badge_Coverage"

## How skipper works

### Configuration
Skipper runs in your cluster, looking for namespaces configured for FIAAS. This is defined as having a ConfigMap named `fiaas-deploy-daemon` in the namespace. The ConfigMap supports two keys:
- `cluster_config.yaml` (required), contains configuration for fiaas-deploy-daemon. You should see the [FIAAS operators guide] for details about this file.
- `tag` (optional, defaults to `stable`). Currently the only valid values are `stable` and `latest`. This controls which version of fiaas-deploy-daemon to deploy to this namespace. See below for more details about what these tags mean.

### fiaas-deploy-daemon tags
- `latest` is the development version of fiaas-deploy-daemon and is updated on every master build. It can break on occasion, and upgrading between `latest` versions may not always work perfectly. You probably only want to use this if you are involved in development and/or testing of fiaas-deploy-daemon.
- `stable` is the version currently considered stable, and is usually promoted from the `latest` version when it has been tested for a while.

### How skipper deploys fiaas-deploy-daemon

When triggered by a request to the `/api/deploy` endpoint, Skipper will list all configured namespaces, and create or update an Application object for fiaas-deploy-daemon in each namespace. This will point to the current `latest` or `stable` image, depending on the value of `tag`.
Skipper relies on fiaas-deploy-daemon to deploy itself, and skipper manages the Application resource which tells fiaas-deploy-daemon how it should deploy iteself. This means that if fiaas-deploy-daemon is not already running in the namespace, it must be bootstrapped first.

#### When fiaas-deploy-daemon not running in namespace (bootstrap)
If fiaas-deploy-daemon isn't running in the namespace, skipper will create/update the Application resource for fiaas-deploy-daemon, including setting the label `fiaas/bootstrap=true`, then create a one-off (`restartPolicy=Never`) pod running fiaas-deploy-daemon in bootstrap mode. In this mode fiaas-deploy-daemon runs with minimal configuration and only deploys Application resources with `fiaas/bootstrap=true` set once and waits for the deployments to be successful, then exits. Then fiaas-deploy-daemon which is now running in normal mode will redeploy itself with full configuration, just as below.

#### When fiaas-deploy-daemon already running
If fiaas-deploy-daemon is already running in the namespace, skipper will update the Application resource for fiaas-deploy-daemon, then fiaas-deploy-daemon will pick up the change and redeploy the new version of itself.

### Updating fiaas-deploy-daemon

To update fiaas-deploy-daemon in a namespace, or in all configured namespaces, use skipper's web interface at `/status`.
It is also possible to use skipper's API directly, see "Deploying fiaas-deploy-daemon to a new namespace" below for details.

#### Automatic updates
When installed with the helm chart value `autoUpdate: true`, skipper will automatically update fiaas-deploy-daemon whenever the configured tag (`stable` or `latest`) is updated. This enables a fully automatic continuous deploy solution for fiaas-deploy-daemon, but means you don't control when or which updates are rolled out. You probably only want to use this if you are involved in development and/or testing of fiaas-deploy-daemon. Use this feature at your own risk.

## How skipper will work differently once currently planned features are completed

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
