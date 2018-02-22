from flask import Flask, Blueprint, make_response
import pinject

web = Blueprint("web", __name__)


@web.route('/')
def hello_world():
    return 'Hello World!'


@web.route('/healthz')
def healthcheck():
    return make_response('', 200)


class WebBindings(pinject.BindingSpec):
    def provide_webapp(self):
        app = Flask(__name__)
        app.register_blueprint(web)
        return app
