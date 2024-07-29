from flask import (
    render_template,
)
from sqlalchemy.exc import SQLAlchemyError
from ..config import (
    app,
)
from db import (
    db_session,
    Game,
    Guide,
)


@app.route("/")
def index():
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
        app.logger.error(f"Database error: {str(e)}")
        return (
            render_template(
                "error.html", error="An error occurred while fetching data."
            ),
            500,
        )


@app.route("/help")
def help():
    return render_template("help.html")