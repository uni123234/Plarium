"""
Routes for the application.

This module defines the routes for the index and help pages, 
and handles fetching data from the database.
"""

from flask import render_template
from sqlalchemy.exc import SQLAlchemyError
from db import db_session, Game, Guide  # Third-party import
from ..config import app  # Local import


@app.route("/")
def index():
    """
    Render the index page with a list of games, guides, and top guides.

    Returns:
        Rendered template of the index page with games, guides, and top guides data.
    """
    try:
        games = db_session.query(Game).all()
        guides = db_session.query(Guide).all()
        top_guides = (
            db_session.query(Guide).order_by(Guide.usage_count.desc()).limit(5).all()
        )
        return render_template(
            "index.html",
            games=games,
            guides=guides,
            top_guides=top_guides,
        )
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        return (
            render_template(
                "error.html", error="An error occurred while fetching data."
            ),
            500,
        )


@app.route("/help")
def help_page():
    """
    Render the help page.

    Returns:
        Rendered template of the help page.
    """
    return render_template("help.html")
