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
from ..config import (
    app,
    tokens,
)
from db import (
    db_session,
    User,
    Guide,
)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")

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
            app.logger.info(f"User {username} registered successfully.")
            return render_template(
                "register.html", message="User registered successfully"
            )
        except IntegrityError:
            db_session.rollback()
            app.logger.warning(
                f"Registration attempt with existing username, email, or phone: {username}, {email}, {phone}."
            )
            return render_template(
                "register.html", error="Username, email, or phone number already exists"
            )
        except SQLAlchemyError as e:
            db_session.rollback()
            app.logger.error(f"Database error: {str(e)}")
            return (
                render_template(
                    "error.html", error="An error occurred during registration."
                ),
                500,
            )

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier")
        password = request.form.get("password")

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

            if user is None or not user.check_password(password):
                app.logger.warning(
                    f"Invalid login attempt for identifier: {identifier}."
                )
                return render_template(
                    "login.html", error="Invalid identifier or password"
                )

            token = secrets.token_urlsafe()
            tokens[user.id] = token

            login_user(user)
            session["token"] = token
            session["logged_in"] = True
            session["user_id"] = user.id
            flash("Login successful", "success")
            app.logger.info(f"User {identifier} logged in successfully.")
            return redirect(url_for("index"))
        except SQLAlchemyError as e:
            app.logger.error(f"Database error: {str(e)}")
            return (
                render_template("error.html", error="An error occurred during login."),
                500,
            )

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    user_id = session.get("user_id")
    try:
        if user_id and user_id in tokens:
            del tokens[user_id]

        session.pop("logged_in", None)
        session.pop("user_id", None)
        session.pop("token", None)
        logout_user()
        flash("You have been logged out", "success")
        app.logger.info(f"User {user_id} logged out successfully.")
        return redirect(url_for("index"))
    except Exception as e:
        app.logger.error(f"Error during logout: {str(e)}")
        return (
            render_template("error.html", error="An error occurred during logout."),
            500,
        )

@app.route("/edit_user", methods=["PUT", "POST"])
@login_required
def edit_user():
    data = request.get_json() or request.form
    user_id = session.get("user_id")

    try:
        user = db_session.query(User).get(user_id)

        if "username" in data:
            user.username = data["username"]
        if "email" in data:
            user.email = data["email"]
        if "phone" in data:
            user.phone = data["phone"]
        if "password" in data:
            user.set_password(data["password"])

        db_session.commit()
        app.logger.info(f"User {user_id} updated successfully.")
        return render_template("edit_user.html", user=user, message="User updated successfully")
    except IntegrityError:
        db_session.rollback()
        app.logger.warning(
            f"Update attempt with existing username, email, or phone for user {user_id}."
        )
        return (
            jsonify({"error": "Username, email, or phone number already exists"}),
            400,
        )
    except SQLAlchemyError as e:
        db_session.rollback()
        app.logger.error(f"Database error: {str(e)}")
        return (
            render_template(
                "error.html", error="An error occurred while updating the user."
            ),
            500,
        )
    

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
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
        app.logger.error(f"Database error: {str(e)}")
        return (
            render_template(
                "error.html", error="An error occurred while fetching user profile."
            ),
            500,
        )
