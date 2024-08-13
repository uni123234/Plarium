"""
Guide-related routes for the application.

This module includes routes for viewing, adding, editing, and deleting guides,
as well as adding new games and viewing guides for games other than 'Raid 
Shadow Legends'.
"""

from flask import (
    jsonify,
    render_template,
    request,
    session,
    Response,
)
from flask_login import login_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from db import db_session, Game, Guide
from ..config import app
from .validators import GuideForm, GameForm


@app.route("/guide/<int:guide_id>", methods=["GET"])
@login_required
def view_guide(guide_id: int) -> Response:
    """
    View a specific guide by its ID.

    This endpoint allows logged-in users to view the details of a guide specified
    by its ID. If the guide is not found, a 404 error is returned. If there is
    a database error during the query, a 500 error is returned.

    Args:
        guide_id (int): The unique identifier of the guide to retrieve.

    Returns:
        Response: Renders the 'view_guide.html' template if the guide is found,
                  otherwise renders the 'error.html' template with a 404 status code.
    """
    try:
        guide = db_session.query(Guide).filter_by(id=guide_id).first()
        if guide is None:
            app.logger.warning("Guide with ID %d not found.", guide_id)
            return (
                render_template(
                    "error.html", error=f"Guide with ID {guide_id} not found."
                ),
                404,
            )

        return render_template("view_guide.html", guide=guide)

    except SQLAlchemyError as error:
        app.logger.error("Database error: %s", str(error))
        return (
            render_template(
                "error.html", error="An error occurred while fetching the guide."
            ),
            500,
        )


@app.route("/help_o_r", methods=["GET", "POST"])
@login_required
def add_guide_all_games() -> Response:
    """
    Add a new guide for a game.

    This endpoint provides functionality for logged-in users to add a new guide
    for a game. The user must provide the game name, title, content, link, video,
    and image. If any required fields are missing or the user is not authenticated,
    an error is returned. Upon successful addition, the user is notified and the
    guide is saved to the database. Handles errors related to database operations
    and integrity.

    Returns:
        Response: Renders the 'help_request_other.html' template with a success
                  message or error.
    """
    form = GuideForm(request.form)  # Create a form instance with the incoming data

    if request.method == "POST":
        if not form.validate():
            app.logger.warning("Guide addition attempt with invalid fields.")
            error_message = "All fields are required"
        else:
            form_data = {
                "game_name": form.game_name.data,
                "title": form.title.data,
                "content": form.content.data,
                "link": form.link.data,
                "video": form.video.data,
                "image": form.image.data,
            }

            user_id = session.get("user_id")
            if not user_id:
                app.logger.warning("Unauthenticated guide addition attempt.")
                return (
                    jsonify({"error": "User not authenticated"}),
                    401,
                )  # Return 401 if the user is not authenticated

            game_name = form_data["game_name"]

            try:
                game = db_session.query(Game).filter_by(name=game_name).first()
                if game is None:
                    app.logger.warning(
                        "Guide addition attempt for non-existent game: %s.", game_name
                    )
                    error_message = f"Game {game_name} not found"
                else:
                    new_guide = Guide(
                        title=form_data["title"],
                        content=form_data["content"],
                        link=form_data["link"],
                        video=form_data["video"],
                        image=form_data["image"],
                        game_id=game.id,
                        user_id=user_id,
                    )
                    db_session.add(new_guide)
                    db_session.commit()
                    app.logger.info(
                        "New guide added successfully for game %s by user %d.",
                        game_name,
                        user_id,
                    )
                    return (
                        render_template(
                            "help_request_other.html",
                            message=f"New guide added successfully for game {game_name}",
                        ),
                        201,
                    )
            except IntegrityError:
                db_session.rollback()
                app.logger.warning(
                    "Guide addition failed due to database integrity error."
                )
                error_message = (
                    "Database error occurred. Please ensure all fields are correct."
                )
            except SQLAlchemyError as error:
                db_session.rollback()
                app.logger.error("Database error: %s", str(error))
                error_message = "An error occurred while adding the guide."

        return render_template("help_request_other.html", error=error_message), 400

    return render_template("help_request_other.html")


@app.route("/add_game", methods=["GET", "POST"])
@login_required
def add_game() -> Response:
    """
    Add a new game.

    This endpoint allows logged-in users to add a new game by providing a game name.
    If the provided game name already exists in the database, an error message is
    returned. On successful addition, a confirmation message is displayed.

    Returns:
        Response: Renders the 'add_game.html' template with a success message or error.
    """
    form = GameForm(request.form)

    if request.method == "POST":
        if not form.validate():
            app.logger.warning("Game addition attempt with invalid fields.")
            return render_template("add_game.html", error="Game name is required")

        game_name = form.game_name.data

        try:
            existing_game = db_session.query(Game).filter_by(name=game_name).first()
            if existing_game:
                app.logger.warning(
                    "Game addition attempt for existing game: %s.", game_name
                )
                return render_template("add_game.html", error="Game already exists")

            game = Game(name=game_name)
            db_session.add(game)
            db_session.commit()
            app.logger.info("New game %s added successfully.", game_name)
            return render_template(
                "add_game.html", message="New game added successfully"
            )

        except IntegrityError:
            db_session.rollback()
            app.logger.warning("Game addition failed due to database integrity error.")
            return (
                render_template(
                    "add_game.html", error="An error occurred while adding the game"
                ),
                400,
            )

        except SQLAlchemyError as error:
            db_session.rollback()
            app.logger.error("Database error: %s", str(error))
            return (
                render_template(
                    "error.html", error="An error occurred while adding the game."
                ),
                500,
            )

    return render_template("add_game.html")


@app.route("/help_o")
def help_other_games() -> Response:
    """
    Display guides for games other than 'Raid Shadow Legends'.

    This endpoint retrieves and displays all guides related to games other than
    'Raid Shadow Legends'. It fetches all games excluding 'Raid Shadow Legends'
    and then collects all guides associated with those games.

    Returns:
        Response: Renders the 'help_other.html' template with a list of guides.
    """
    try:
        games = db_session.query(Game).filter(Game.name != "Raid Shadow Legends").all()
        other_guides = [
            guide
            for game in games
            for guide in db_session.query(Guide).filter_by(game_id=game.id).all()
        ]

        return render_template("help_other.html", guides=other_guides)

    except SQLAlchemyError as error:
        app.logger.error("Database error: %s", str(error))
        return (
            render_template(
                "error.html",
                error="An error occurred while fetching guides for other games.",
            ),
            500,
        )
