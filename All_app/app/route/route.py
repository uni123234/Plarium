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
from sqlalchemy.exc import IntegrityError
from .config import login_manager, app, db_session, User, Game, Guide , tokens, load_user, make_session_permanent
import secrets


@app.route("/")
def index():
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


@app.route("/guide/<int:guide_id>", methods=["GET"])
@login_required
def view_guide(guide_id):
    guide = db_session.query(Guide).filter_by(id=guide_id).first()
    if not guide:
        return (
            render_template("error.html", error=f"Guide with ID {guide_id} not found."),
            404,
        )
    return render_template("view_guide.html", guide=guide)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")

        if not all([username, email, phone, password]):
            return render_template(
                "register.html",
                error="Username, email, phone, and password are required",
            )

        user = User(username=username, email=email, phone=phone)
        user.set_password(password)
        db_session.add(user)

        try:
            db_session.commit()
        except IntegrityError:
            db_session.rollback()
            return render_template(
                "register.html", error="Username, email, or phone number already exists"
            )

        return render_template("register.html", message="User registered successfully")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier")
        password = request.form.get("password")

        if not all([identifier, password]):
            return render_template(
                "login.html", error="Identifier and password are required"
            )

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
            return render_template("login.html", error="Invalid identifier or password")

        token = secrets.token_urlsafe()
        tokens[user.id] = token

        login_user(user)
        session["token"] = token
        session["logged_in"] = True
        session["user_id"] = user.id
        flash("Login successful", "success")
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    user_id = session.get("user_id")
    if user_id and user_id in tokens:
        del tokens[user_id]

    session.pop("logged_in", None)
    session.pop("user_id", None)
    session.pop("token", None)
    logout_user()
    flash("You have been logged out", "success")
    return redirect(url_for("index"))


@app.route("/edit_user", methods=["PUT", "POST"])
@login_required
def edit_user():
    data = request.get_json() or request.form
    user_id = session.get("user_id")

    user = db_session.query(User).get(user_id)

    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]
    if "phone" in data:
        user.phone = data["phone"]
    if "password" in data:
        user.set_password(data["password"])

    try:
        db_session.commit()
    except IntegrityError:
        db_session.rollback()
        return (
            jsonify({"error": "Username, email, or phone number already exists"}),
            400,
        )

    return render_template("edit_user.html", message="User updated successfully")


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
            return jsonify({"error": "User not authenticated"}), 401

        if not all([game_name, title, content, link, video, image]):
            return (
                render_template(
                    "help_request_other.html", error="All fields are required"
                ),
                400,
            )

        game = db_session.query(Game).filter_by(name=game_name).first()
        if not game:
            return (
                render_template(
                    "help_request_other.html", error=f"Game {game_name} not found"
                ),
                404,
            )

        try:
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

        except IntegrityError as e:
            db_session.rollback()
            return (
                render_template(
                    "help_request_onother.html",
                    error="Database error occurred. Please ensure all fields are correct.",
                ),
                400,
            )

        return (
            render_template(
                "help_request_other.html",
                message=f"New guide added successfully for game {game_name}",
            ),
            201,
        )

    return render_template("help_request_other.html")


@app.route("/add_game", methods=["GET", "POST"])
@login_required
def add_game():
    if request.method == "POST":
        game_name = request.form.get("game_name")

        if not game_name:
            return render_template("add_game.html", error="Game name is required")

        existing_game = db_session.query(Game).filter_by(name=game_name).first()
        if existing_game:
            return render_template("add_game.html", error="Game already exists")

        game = Game(name=game_name)
        db_session.add(game)

        try:
            db_session.commit()
            return render_template(
                "add_game.html", message="New game added successfully"
            )
        except IntegrityError:
            db_session.rollback()
            return render_template(
                "add_game.html", error="An error occurred while adding the game"
            )

    return render_template("add_game.html")


@app.route("/help_o")
def help_other_games():
    games = db_session.query(Game).filter(Game.name != "Raid Shadow Legends").all()

    other_guides = []
    for game in games:
        guides = db_session.query(Guide).filter_by(game_id=game.id).all()
        other_guides.extend(guides)

    return render_template("help_other.html", other_guides=other_guides)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
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


@app.route("/edit_guide/<int:guide_id>", methods=["GET", "POST"])
@login_required
def edit_guide(guide_id):
    guide = db_session.query(Guide).get(guide_id)
    if not guide or guide.user_id != session.get("user_id"):
        return jsonify({"error": "Guide not found or not authorized"}), 404

    if request.method == "POST":
        guide.title = request.form.get("title")
        guide.content = request.form.get("content")
        guide.link = request.form.get("link")
        guide.video = request.form.get("video")
        guide.image = request.form.get("image")
        db_session.commit()
        return redirect(url_for("profile"))

    return render_template("edit_guide_form.html", guide=guide)


@app.route("/delete_guide/<int:guide_id>")
@login_required
def delete_guide(guide_id):
    guide = db_session.query(Guide).get(guide_id)
    if not guide or guide.user_id != session.get("user_id"):
        return jsonify({"error": "Guide not found or not authorized"}), 404

    db_session.delete(guide)
    db_session.commit()
    return redirect(url_for("profile"))
