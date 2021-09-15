#!/usr/bin/env python
# -*- coding: utf-8

# Copyright 2017-2019 The FIAAS Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import logging

from k8s.client import NotFound
from k8s.models.common import ObjectMeta
from k8s.models.role import Role, PolicyRule
from k8s.models.role_binding import RoleBinding, RoleRef, Subject

NAME = "fiaas-deploy-daemon"

LOG = logging.getLogger(__name__)


def deploy_rbac(namespace):
    LOG.info("Deploying RBAC resources in %s", namespace)
    try:
        Role.delete(name=NAME, namespace=namespace)
    except NotFound:
        pass
    metadata = _create_metadata(namespace)
    rules = _create_policy_rules()
    role = Role(metadata=metadata, rules=rules)
    role.save()

    try:
        RoleBinding.delete(name=NAME, namespace=namespace)
    except NotFound:
        pass
    role_binding = _create_role_binding(namespace)
    role_binding.save()


def _create_role_binding(namespace):
    metadata = _create_metadata(namespace)
    return RoleBinding(
        metadata=metadata,
        roleRef=RoleRef(apiGroup="rbac.authorization.k8s.io", kind="Role", name=NAME),
        subjects=[Subject(kind="ServiceAccount", name=NAME, namespace=namespace)],
    )


def _create_policy_rules():
    return [
        PolicyRule(
            apiGroups=["fiaas-schibsted.io", "schibsted.io"],
            resources=["applications", "application-statuses", "statuses"],
            verbs=["create", "delete", "get", "list", "update", "watch"],
        ),
        PolicyRule(
            apiGroups=[
                "",
                "apps",
                "autoscaling",
                "apiextensions",
                "apiextensions.k8s.io",
                "extensions"
            ],
            resources=[
                "configmaps",
                "customresourcedefinitions",
                "deployments",
                "horizontalpodautoscalers",
                "ingresses",
                "pods",
                "resourcequotas",
                "services",
            ],
            verbs=["create", "delete", "get", "list", "update", "watch", "deletecollection"],
        ),
        PolicyRule(
            apiGroups=[""],
            resources=["serviceaccounts"],
            verbs=["create", "delete", "get", "list", "update"],
        )
    ]


def _create_metadata(namespace):
    labels = {"app": NAME}
    return ObjectMeta(name=NAME, labels=labels, namespace=namespace)
