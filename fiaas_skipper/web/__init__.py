import json

import pinject
from flask import Flask, Blueprint, make_response

from ..deploy.deploy import Deployment

web = Blueprint("web", __name__)


@web.route('/')
def hello_world():
    return 'Hello World!'


@web.route('/status')
def status():
    deployments = web.cluster.find_deployments('fiaas-deploy-daemon')
    return make_response(json.dumps(deployments, default=_encode_deployment), 200)


def _encode_deployment(obj):
    if isinstance(obj, Deployment):
        return obj.__dict__
    return obj


@web.route('/healthz')
def healthcheck():
    return make_response('', 200)


@web.route('/deploy', methods=['POST'])
def deploy():
    web.deployer.deploy()
    return make_response('', 200)


class WebBindings(pinject.BindingSpec):
    def provide_webapp(self, deployer, cluster):
        app = Flask(__name__)
        app.register_blueprint(web)
        web.cluster = cluster
        web.deployer = deployer
        return app
