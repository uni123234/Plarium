import logging, secrets, os
from logging.handlers import RotatingFileHandler
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
from .config import (
    app,
    db_session,
    User,
    Game,
    Guide,
    tokens,
)

if not os.path.exists("logs"):
    os.makedirs("logs")

handler = RotatingFileHandler("logs/application.log", maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
app.logger.addHandler(handler)


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


@app.route("/help")
def help():
    return render_template("help.html")


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


