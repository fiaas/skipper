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

### How skipper will work differently once currently planned features are completed

We are not done. We have planned some further features, which will improve the experience of using Skipper significantly. Here are some of the planned changes:

* Skipper will detect when new versions of fiaas-deploy-daemon is available, and automatically update all configured namespaces with the new version. This enables a fully automatic continuous deploy solution for fiaas-deploy-daemon.
* Try to detect when an instance of fiaas-deploy-daemon is not operating properly, and re-deploy it
* Allow operators to force an update, even if Skipper thinks everything is ok

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
    

[FIAAS operators guide]: https://github.com/fiaas/fiaas-deploy-daemon/blob/master/docs/operator_guide.md
