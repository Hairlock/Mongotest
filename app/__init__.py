#sys.path.insert(1, os.path.join(os.path.abspath('.'), 'mongotest/lib/python2.7/site-packages'))

from flask import Flask
from flask.ext.mongoengine import MongoEngine
from werkzeug.contrib.fixers import ProxyFix

app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {'DB': "my_tumble_log"}
app.config["SECRET_KEY"] = "KeepThisS3cr3t"
app.url_map.strict_slashes = False

app.wsgi_app = ProxyFix(app.wsgi_app)

db = MongoEngine(app)

from site.admin import admin


def register_blueprints(app):
    from site.views import posts

    app.register_blueprint(posts)
    app.register_blueprint(admin)

register_blueprints(app)