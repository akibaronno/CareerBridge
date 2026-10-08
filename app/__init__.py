"""CareerBridge - creates the Flask app and wires everything together."""
import os

from flask import Flask

from config import Config
from app.extensions import db, login_manager
from app.constants import STATUS_COLORS

app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db.init_app(app)
login_manager.init_app(app)
app.jinja_env.globals.update(STATUS_COLORS=STATUS_COLORS)  # macros need this global

# These imports must stay at the bottom: they use `app` defined above.
from app import models, routes  # noqa: E402,F401
