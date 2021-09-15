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
import os
from argparse import Namespace

import configargparse

DEFAULT_CONFIG_FILE = "/var/run/config/fiaas/cluster_config.yaml"
DEFAULT_OVERRIDE_SPEC_FILE = "/var/run/config/fiaas/fiaas_override.yaml"


class Configuration(Namespace):
    VALID_LOG_FORMAT = ("plain", "json")

    def __init__(self, args=None, **kwargs):
        super(Configuration, self).__init__(**kwargs)
        self._logger = logging.getLogger(__name__)
        self._parse_args(args)
        self._resolve_api_config()

    def _parse_args(self, args):
        parser = configargparse.ArgParser(auto_env_var_prefix="",
                                          add_config_file_help=False,
                                          add_env_var_help=False,
                                          config_file_parser_class=configargparse.YAMLConfigFileParser,
                                          default_config_files=[DEFAULT_CONFIG_FILE],
                                          args_for_setting_config_path=["-c", "--config-file"],
                                          ignore_unknown_config_file_keys=True,
                                          description="%(prog)s deploys applications to Kubernetes",
                                          formatter_class=configargparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument("--log-format", help="Set logformat (default: %(default)s)", choices=self.VALID_LOG_FORMAT,
                            default="plain")
        parser.add_argument("--debug", help="Enable a number of debugging options (including disable SSL-verification)",
                            action="store_true")
        parser.add_argument("--port", help="Port to use for the web-interface (default: %(default)s)", type=int,
                            default=5000)
        parser.add_argument("--baseurl", help="Url to server hosting release channel meta data.",
                            default="http://fiaas-release.delivery-pro.schibsted.io")
        parser.add_argument("--release-channel-metadata",
                            help="Provide hardcoded release channel metadata (Used for debugging purposes).")
        parser.add_argument("--release-channel-metadata-spec",
                            help="Provide hardcoded spec file (Used for debugging purposes).")
        parser.add_argument("--spec-file-override",
                            help="File containing overrides of values in release channel spec file.",
                            default=DEFAULT_OVERRIDE_SPEC_FILE)
        parser.add_argument("--disable-autoupdate", help="Disable auto updating of fiaas-deploy-daemon.",
                            action="store_true")
        parser.add_argument("--status-update-interval", help="How frequently to check status of namespaces.", type=int,
                            default=30)
        parser.add_argument("--rbac", help="Create RBAC resources when deploying fiaas-deploy-daemon",
                            action="store_true", default=False)
        api_parser = parser.add_argument_group("API server")
        api_parser.add_argument("--api-server", help="Address of the api-server to use (IP or name)",
                                default="https://kubernetes.default.svc.cluster.local")
        api_parser.add_argument("--api-token", help="Token to use (default: lookup from service account)", default=None)
        api_parser.add_argument("--api-cert", help="API server certificate (default: lookup from service account)",
                                default=None)
        client_cert_parser = parser.add_argument_group("Client certificate")
        client_cert_parser.add_argument("--client-cert", help="Client certificate to use", default=None)
        client_cert_parser.add_argument("--client-key", help="Client certificate key to use", default=None)
        parser.parse_args(args, namespace=self)

    def _resolve_api_config(self):
        token_file = "/var/run/secrets/kubernetes.io/serviceaccount/token"
        if os.path.exists(token_file):
            with open(token_file) as fobj:
                self.api_token = fobj.read().strip()
            self.api_cert = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"

    def __repr__(self):
        return "Configuration({})".format(
            ", ".join("{}={}".format(key, self.__dict__[key]) for key in vars(self)
                      if not key.startswith("_") and not key.isupper() and "token" not in key)
        )
