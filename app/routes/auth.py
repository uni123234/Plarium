"""
Authentication routes for user registration, login, logout, and profile management.
"""

import secrets
from flask import (
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import (
    current_user,
    login_user,
    logout_user,
    login_required,
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.utils import update_user_info
from db import db_session, User, Guide
from ..config import app, tokens


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Handle user registration. If the request method is POST,
    process the registration form; otherwise, render the registration page.
    """
    if request.method == "POST":
        username, email, phone, password = [
            request.form.get(field)
            for field in ["username", "email", "phone", "password"]
        ]

        if not all([username, email, phone, password]):
            app.logger.warning("Registration attempt with missing fields.")
            return render_template(
                "register.html",
                error="Username, email, phone, and password are required",
            )

        user = User(username=username, email=email, phone=phone)
        user.set_password(password)
        db_session.add(user)

        try:
            db_session.commit()
            app.logger.info("User %s registered successfully.", username)
            return render_template(
                "register.html", message="User registered successfully"
            )
        except IntegrityError:
            db_session.rollback()
            app.logger.warning(
                "Registration attempt with existing username, email, or phone: %s, %s, %s.",
                username,
                email,
                phone,
            )
            return render_template(
                "register.html", error="Username, email, or phone number already exists"
            )
        except SQLAlchemyError as e:
            db_session.rollback()
            app.logger.error("Database error: %s", e)
            return (
                render_template(
                    "error.html", error="An error occurred during registration."
                ),
                500,
            )

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login. Process the login form for POST requests;
    otherwise, render the login page.
    """
    if request.method == "POST":
        # Fetch form data in one line
        identifier, password = [
            request.form.get(field) for field in ["identifier", "password"]
        ]

        if not all([identifier, password]):
            app.logger.warning("Login attempt with missing fields.")
            return render_template(
                "login.html", error="Identifier and password are required"
            )

        try:
            user = (
                db_session.query(User)
                .filter(
                    (User.username == identifier)
                    | (User.email == identifier)
                    | (User.phone == identifier)
                )
                .first()
            )

            if not user or not user.check_password(password):
                app.logger.warning(
                    "Invalid login attempt for identifier: %s.", identifier
                )
                return render_template(
                    "login.html", error="Invalid identifier or password"
                )

            token = secrets.token_urlsafe()
            tokens[user.id] = token

            login_user(user)
            session.update({"token": token, "logged_in": True, "user_id": user.id})
            flash("Login successful", "success")
            app.logger.info("User %s logged in successfully.", identifier)
            return redirect(url_for("index"))

        except SQLAlchemyError as e:
            app.logger.error("Database error: %s", e)
            return (
                render_template("error.html", error="An error occurred during login."),
                500,
            )

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """
    Handle user logout. Removes session data and tokens, then logs the user out.
    """
    user_id = session.pop("user_id", None)
    try:
        if user_id:
            tokens.pop(user_id, None)

        session.pop("logged_in", None)
        session.pop("token", None)

        logout_user()

        flash("You have been logged out", "success")
        app.logger.info("User %s logged out successfully.", user_id)
        return redirect(url_for("index"))
    except SQLAlchemyError as e:
        app.logger.error("Database error during logout: %s", e)
        return (
            render_template("error.html", error="An error occurred during logout."),
            500,
        )


@app.route("/edit_user", methods=["POST"])
@login_required
def edit_user():
    """
    Handle user profile update. Updates user details based on the submitted data.
    """
    data = request.get_json() or request.form
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "User ID is missing"}), 400

    try:
        user = db_session.query(User).get(user_id)
        if user is None:
            return jsonify({"error": "User not found"}), 404

        update_user_info(user, data)
        db_session.commit()

        app.logger.info("User %s updated successfully.", user_id)
        flash("User updated successfully", "success")
        return render_template("edit_user.html", user=user)

    except IntegrityError:
        db_session.rollback()
        app.logger.warning(
            "Update attempt with existing username, email, or phone for user %s.",
            user_id,
        )
        return (
            jsonify({"error": "Username, email, or phone number already exists"}),
            400,
        )

    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error("Database error: %s", e)
        return (
            render_template(
                "error.html", error="An error occurred while updating the user."
            ),
            500,
        )


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """
    Render the user profile page. Optionally filter guides by search query.
    """
    try:
        search_query = request.args.get("search", "")
        if search_query:
            guides = (
                db_session.query(Guide)
                .filter(
                    Guide.user_id == current_user.id, Guide.title.contains(search_query)
                )
                .all()
            )
        else:
            guides = db_session.query(Guide).filter_by(user_id=current_user.id).all()
        return render_template("profile.html", user=current_user, guides=guides)
    except SQLAlchemyError as e:
        app.logger.error("Database error: %s", e)
        return (
            render_template(
                "error.html", error="An error occurred while fetching user profile."
            ),
            500,
        )
