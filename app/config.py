"""
This module sets up the Flask application, configures session settings,
and initializes the login manager.
"""

from datetime import timedelta
import logging

from flask import Flask, session
from flask_login import LoginManager

from db import db_session, User


app = Flask(
    __name__, template_folder="frontend/templates", static_folder="frontend/static"
)
app.secret_key = "supersecretkey"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

logging.basicConfig(level=logging.DEBUG)

tokens = {}

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    """
    Loads the user by ID for Flask-Login.

    Args:
        user_id (int): The user ID.

    Returns:
        User: The user object or None if not found.
    """
    return db_session.query(User).get(int(user_id))


@app.before_request
def make_session_permanent():
    """
    Ensures that the session is marked as permanent before each request.
    """
    session.permanent = True
