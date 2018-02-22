from flask import Flask, Blueprint
import pinject

web = Blueprint("web", __name__)


@web.route('/')
def hello_world():
    return 'Hello World!'


class WebBindings(pinject.BindingSpec):
    def provide_webapp(self):
        app = Flask(__name__)
        app.register_blueprint(web)
        return app
