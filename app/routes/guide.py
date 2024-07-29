import logging, os
from logging.handlers import RotatingFileHandler
from flask import (
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import (
    login_required,
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from ..config import (
    app,
)
from db import (
    db_session,
    Game,
    Guide,
)


@app.route("/guide/<int:guide_id>", methods=["GET"])
@login_required
def view_guide(guide_id):
    try:
        guide = db_session.query(Guide).filter_by(id=guide_id).first()
        if not guide:
            app.logger.warning(f"Guide with ID {guide_id} not found.")
            return (
                render_template(
                    "error.html", error=f"Guide with ID {guide_id} not found."
                ),
                404,
            )
        return render_template("view_guide.html", guide=guide)
    except SQLAlchemyError as e:
        app.logger.error(f"Database error: {str(e)}")
        return (
            render_template(
                "error.html", error="An error occurred while fetching the guide."
            ),
            500,
        )


@app.route("/help_o_r", methods=["GET", "POST"])
@login_required
def add_guide_all_games():
    if request.method == "POST":
        game_name = request.form.get("game_name")
        title = request.form.get("title")
        content = request.form.get("content")
        link = request.form.get("link")
        video = request.form.get("video")
        image = request.form.get("image")

        user_id = session.get("user_id")
        if not user_id:
            app.logger.warning("Unauthenticated guide addition attempt.")
            return jsonify({"error": "User not authenticated"}), 401

        if not all([game_name, title, content, link, video, image]):
            app.logger.warning("Guide addition attempt with missing fields.")
            return (
                render_template(
                    "help_request_other.html", error="All fields are required"
                ),
                400,
            )

        try:
            game = db_session.query(Game).filter_by(name=game_name).first()
            if not game:
                app.logger.warning(
                    f"Guide addition attempt for non-existent game: {game_name}."
                )
                return (
                    render_template(
                        "help_request_other.html", error=f"Game {game_name} not found"
                    ),
                    404,
                )

            new_guide = Guide(
                title=title,
                content=content,
                link=link,
                video=video,
                image=image,
                game_id=game.id,
                user_id=user_id,
            )
            db_session.add(new_guide)
            db_session.commit()
            app.logger.info(
                f"New guide added successfully for game {game_name} by user {user_id}."
            )
            return (
                render_template(
                    "help_request_other.html",
                    message=f"New guide added successfully for game {game_name}",
                ),
                201,
            )
        except IntegrityError as e:
            db_session.rollback()
            app.logger.warning("Guide addition failed due to database integrity error.")
            return (
                render_template(
                    "help_request_other.html",
                    error="Database error occurred. Please ensure all fields are correct.",
                ),
                400,
            )
        except SQLAlchemyError as e:
            db_session.rollback()
            app.logger.error(f"Database error: {str(e)}")
            return (
                render_template(
                    "help_request_other.html",
                    error="An error occurred while adding the guide.",
                ),
                500,
            )

    return render_template("help_request_other.html")


@app.route("/add_game", methods=["GET", "POST"])
@login_required
def add_game():
    if request.method == "POST":
        game_name = request.form.get("game_name")

        if not game_name:
            app.logger.warning("Game addition attempt with missing fields.")
            return render_template("add_game.html", error="Game name is required")

        try:
            existing_game = db_session.query(Game).filter_by(name=game_name).first()
            if existing_game:
                app.logger.warning(
                    f"Game addition attempt for existing game: {game_name}."
                )
                return render_template("add_game.html", error="Game already exists")

            game = Game(name=game_name)
            db_session.add(game)

            db_session.commit()
            app.logger.info(f"New game {game_name} added successfully.")
            return render_template(
                "add_game.html", message="New game added successfully"
            )
        except IntegrityError:
            db_session.rollback()
            app.logger.warning("Game addition failed due to database integrity error.")
            return render_template(
                "add_game.html", error="An error occurred while adding the game"
            )
        except SQLAlchemyError as e:
            db_session.rollback()
            app.logger.error(f"Database error: {str(e)}")
            return (
                render_template(
                    "error.html", error="An error occurred while adding the game."
                ),
                500,
            )

    return render_template("add_game.html")


@app.route("/help_o")
def help_other_games():
    try:
        games = db_session.query(Game).filter(Game.name != "Raid Shadow Legends").all()

        other_guides = []
        for game in games:
            guides = db_session.query(Guide).filter_by(game_id=game.id).all()
            other_guides.extend(guides)

        return render_template("help_other.html", other_guides=other_guides)
    except SQLAlchemyError as e:
        app.logger.error(f"Database error: {str(e)}")
        return (
            render_template(
                "error.html", error="An error occurred while fetching other games."
            ),
            500,
        )


@app.route("/edit_guide/<int:guide_id>", methods=["GET", "POST"])
@login_required
def edit_guide(guide_id):
    try:
        guide = db_session.query(Guide).get(guide_id)
        if not guide or guide.user_id != session.get("user_id"):
            app.logger.warning(
                f"Unauthorized guide edit attempt for guide ID: {guide_id}."
            )
            return jsonify({"error": "Guide not found or not authorized"}), 404

        if request.method == "POST":
            guide.title = request.form.get("title")
            guide.content = request.form.get("content")
            guide.link = request.form.get("link")
            guide.video = request.form.get("video")
            guide.image = request.form.get("image")
            db_session.commit()
            app.logger.info(
                f"Guide {guide_id} edited successfully by user {session.get('user_id')}."
            )
            return redirect(url_for("profile"))

        return render_template("edit_guide_form.html", guide=guide)
    except SQLAlchemyError as e:
        app.logger.error(f"Database error: {str(e)}")
        return (
            render_template(
                "error.html", error="An error occurred while editing the guide."
            ),
            500,
        )


@app.route("/delete_guide/<int:guide_id>")
@login_required
def delete_guide(guide_id):
    try:
        guide = db_session.query(Guide).get(guide_id)
        if not guide or guide.user_id != session.get("user_id"):
            app.logger.warning(
                f"Unauthorized guide deletion attempt for guide ID: {guide_id}."
            )
            return jsonify({"error": "Guide not found or not authorized"}), 404

        db_session.delete(guide)
        db_session.commit()
        app.logger.info(
            f"Guide {guide_id} deleted successfully by user {session.get('user_id')}."
        )
        return redirect(url_for("profile"))
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error(f"Database error: {str(e)}")
        return (
            render_template(
                "error.html", error="An error occurred while deleting the guide."
            ),
            500,
        )


