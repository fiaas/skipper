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
    res = []
    configmaps = ConfigMap.list()
    for c in configmaps:
        if c.metadata.name == 'fiaas-deploy-daemon':
            version = c.data.version if 'version' in c.data else 'stable'
            dep = Deployment.get(name='fiaas-deploy-daemon', namespace=c.metadata.namespace)
            res.append({
                'namespace': c.metadata.namespace,
                'version': version,
                'status': 'available' if dep.status.availableReplicas >= dep.spec.replicas else 'unavailable'
            })
    return make_response(json.dumps(res), 200)


@web.route('/healthz')
def healthcheck():
    return make_response('', 200)


class WebBindings(pinject.BindingSpec):
    def provide_webapp(self):
        app = Flask(__name__)
        app.register_blueprint(web)
        return app
