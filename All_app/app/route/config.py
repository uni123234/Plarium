from datetime import timedelta
import logging
from flask import Flask
from flask_login import LoginManager
from ...db.db import session as db_session, User, Guide, Game


app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
tokens = {}
logging.basicConfig(level=logging.DEBUG)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
