from flask import Flask, jsonify, render_template, request
from functools import wraps
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from ...db.db import User, session, Game, Guide, PilariumGuide

app = Flask(__name__)
tokens = {}


def login_required(f):
    """
    Decorator to ensure that the user is logged in.
    Checks if the Authorization token is valid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or token not in tokens.values():
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """
    Main index route that renders the home page with lists of games and guides.
    """
    games = session.query(Game).all()
    guides = session.query(Guide).all()
    pilarium_guides = session.query(PilariumGuide).all()
    top_guides = session.query(Guide).order_by(Guide.usage_count.desc()).limit(5).all()
    top_pilarium_guides = session.query(PilariumGuide).order_by(PilariumGuide.usage_count.desc()).limit(5).all()
    return render_template('index.html', games=games, guides=guides, pilarium_guides=pilarium_guides,
                           top_guides=top_guides, top_pilarium_guides=top_pilarium_guides)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Route to register a new user.
    Handles form submission with fields: username, email, phone, and password.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')

        # Validate request data
        if not all([username, email, phone, password]):
            return render_template('register.html', error='Username, email, phone, and password are required')

        user = User(username=username, email=email, phone=phone)
        user.set_password(password)
        session.add(user)

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return render_template('register.html', error='Username, email, or phone number already exists')

        return render_template('register.html', message='User registered successfully')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Route to log in an existing user.
    Handles form submission with fields: identifier (username, email, or phone) and password.
    """
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')

        # Validate request data
        if not all([identifier, password]):
            return render_template('login.html', error='Identifier and password are required')

        user = session.query(User).filter(
            (User.username == identifier) |
            (User.email == identifier) |
            (User.phone == identifier)
        ).first()

        if user is None or not user.check_password(password):
            return render_template('login.html', error='Invalid identifier or password')

        token = generate_password_hash(identifier + password)
        tokens[user.id] = token

        return render_template('login.html', message='Login successful', token=token)

    return render_template('login.html')


@app.route('/edit_user', methods=['PUT', 'POST'])
@login_required
def edit_user():
    """
    Route to edit user details.
    Handles form submission or JSON payload with optional fields: username, email, phone, password.
    """
    data = request.get_json() or request.form
    token = request.headers.get('Authorization')
    user_id = [key for key, value in tokens.items() if value == token][0]

    user = session.query(User).get(user_id)

    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']
    if 'phone' in data:
        user.phone = data['phone']
    if 'password' in data:
        user.set_password(data['password'])

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return jsonify({'error': 'Username, email, or phone number already exists'}), 400

    return render_template('edit_user.html', message='User updated successfully')


@app.route('/help')
def help():
    """
    Route to render the help page.
    """
    return render_template('help.html')


@app.route('/helps_p_r', methods=['GET', 'POST'])
def add_guide_pilarium():
    """
    Route to add a new guide for "Raid Shadow Legends".
    Handles form submission with fields: content, link, video, and image.
    """
    if request.method == 'POST':
        content = request.form.get('content')
        link = request.form.get('link')
        video = request.form.get('video')
        image = request.form.get('image')

        # Validate request data
        if not all([content, link, video, image]):
            return render_template('help_raid_sl_request.html', error='Content, link, video, and image are required'), 400

        game_name = "Raid Shadow Legends"
        game = session.query(Game).filter_by(name=game_name).first()
        if not game:
            return render_template('help_raid_sl_request.html', error=f'Game {game_name} not found'), 404

        new_guide = PilariumGuide(content=content, link=link, video=video, image=image)
        game.guides.append(new_guide)
        session.add(new_guide)
        session.commit()

        return render_template('help_raid_sl_request.html', message='New guide added successfully for Raid Shadow Legends'), 201

    return render_template('help_raid_sl_request.html')



@app.route('/help_o_r', methods=['GET', 'POST'])
def add_guide_all_games():
    """
    Route to add a new guide for any game.
    Handles form submission with fields: game_name, content, link, video, and image.
    """
    if request.method == 'POST':
        game_name = request.form.get('game_name')
        content = request.form.get('content')
        link = request.form.get('link')
        video = request.form.get('video')
        image = request.form.get('image')

        # Validate request data
        if not all([game_name, content, link, video, image]):
            return render_template('help_request_onother.html', error='All fields are required'), 400

        game = session.query(Game).filter_by(name=game_name).first()
        if not game:
            return render_template('help_request_onother.html', error=f'Game {game_name} not found'), 404

        new_guide = Guide(content=content, link=link, video=video, image=image, game_id=game.id)
        game.guides.append(new_guide)
        session.add(new_guide)
        session.commit()

        return render_template('help_request_onother.html', message=f'New guide added successfully for game {game_name}'), 201

    return render_template('help_request_onother.html')



@app.route('/help_p')
def help_p():
    """
    Route to render the help page specifically for "Raid Shadow Legends" guides.
    """
    game_name = "Raid Shadow Legends"
    game = session.query(Game).filter_by(name=game_name).first()
    
    if not game:
        return jsonify({'error': f'Game {game_name} not found'}), 404

    guides = session.query(PilariumGuide).all()
    
    return render_template('help_raid_sl.html', guides=guides)


@app.route('/help_o')
def help_o():
    """
    Route to render the help page for all other games excluding "Raid Shadow Legends".
    """
    guides = session.query(Guide).join(Game).filter(Game.name != "Raid Shadow Legends").all()
    
    return render_template('help_onother.html', guides=guides)


@app.route('/edit_guide/<int:guide_id>', methods=['GET', 'POST'])
@login_required
def edit_guide(guide_id):
    """
    Route to edit an existing guide.
    Handles form submission with fields: content, link, video, image.
    """
    guide = session.query(Guide).get(guide_id)

    if not guide:
        return render_template('error.html', message='Guide not found'), 404

    if request.method == 'POST':
        content = request.form.get('content')
        link = request.form.get('link')
        video = request.form.get('video')
        image = request.form.get('image')

        if content:
            guide.content = content
        if link:
            guide.link = link
        if video:
            guide.video = video
        if image:
            guide.image = image

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return render_template('edit_guide.html', guide=guide, error='An error occurred while updating the guide'), 400

        guides = session.query(Guide).all()
        return render_template('helps_manager.html', guides=guides, message='Guide updated successfully'), 200

    return render_template('edit_guide.html', guide=guide)



@app.route('/edit_pilarium_guide/<int:guide_id>', methods=['GET', 'POST'])
@login_required
def edit_pilarium_guide(guide_id):
    """
    Route to edit an existing Pilarium guide.
    Handles form submission with fields: content, link, video, image.
    """
    guide = session.query(PilariumGuide).get(guide_id)

    if not guide:
        return render_template('error.html', message='Guide not found'), 404

    if request.method == 'POST':
        content = request.form.get('content')
        link = request.form.get('link')
        video = request.form.get('video')
        image = request.form.get('image')

        if content:
            guide.content = content
        if link:
            guide.link = link
        if video:
            guide.video = video
        if image:
            guide.image = image

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return render_template('edit_guide.html', guide=guide, error='An error occurred while updating the guide'), 400

        pilarium_guides = session.query(PilariumGuide).all()
        return render_template('helps_manager.html', pilarium_guides=pilarium_guides, message='Pilarium guide updated successfully'), 200

    return render_template('edit_guide.html', guide=guide)



@app.route('/profile', methods=['GET'])
@login_required
def profile():
    """
    Route to render the user's profile page with all guides created by the user.
    """
    token = request.headers.get('Authorization')
    user_id = [key for key, value in tokens.items() if value == token][0]

    user = session.query(User).get(user_id)
    guides = session.query(Guide).filter_by(user_id=user_id).all()
    pilarium_guides = session.query(PilariumGuide).filter_by(user_id=user_id).all()

    return render_template('profile.html', user=user, guides=guides, pilarium_guides=pilarium_guides)
