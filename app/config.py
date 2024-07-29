from datetime import timedelta
import logging
from flask import Flask, session
from flask_login import LoginManager
from db.db import session as db_session, User


app = Flask(__name__, template_folder="frontend/templates", static_folder="frontend/static")
app.secret_key = "supersecretkey"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
tokens = {}
logging.basicConfig(level=logging.DEBUG)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db_session.query(User).get(int(user_id))


@app.before_request
def make_session_permanent():
    session.permanent = True
