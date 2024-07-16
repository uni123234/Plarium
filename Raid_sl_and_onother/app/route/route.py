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
    Expects a JSON payload with username, email, phone, and password.
    """
    if request.method == 'POST':
        data = request.get_json() or request.form

        # Validate request data
        if not all(key in data for key in ('username', 'email', 'phone', 'password')):
            return render_template('register.html', error='Username, email, phone, and password are required')

        user = User(username=data['username'], email=data['email'], phone=data['phone'])
        user.set_password(data['password'])
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
    Expects a JSON payload with identifier (username, email, or phone) and password
    or form data with identifier and password.
    """
    if request.method == 'POST':
        data = request.get_json() or request.form

        # Validate request data
        if not all(key in data for key in ('identifier', 'password')):
            return render_template('login.html', error='Identifier and password are required')

        user = session.query(User).filter(
            (User.username == data['identifier']) |
            (User.email == data['identifier']) |
            (User.phone == data['identifier'])
        ).first()

        if user is None or not user.check_password(data['password']):
            return render_template('login.html', error='Invalid identifier or password')

        token = generate_password_hash(data['identifier'] + data['password'])
        tokens[user.id] = token

        return render_template('login.html', message='Login successful', token=token)

    return render_template('login.html')


@app.route('/edit_user', methods=['PUT'])
@login_required
def edit_user():
    """
    Route to edit user details.
    Expects a JSON payload with optional fields: username, email, phone, password.
    """
    data = request.get_json()
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

    return jsonify({'message': 'User updated successfully'}), 200


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """
    Route to request a password reset.
    Expects a JSON payload with identifier (username, email, or phone).
    """
    if request.method == 'POST':
        data = request.get_json() or request.form

        # Validate request data
        if 'identifier' not in data:
            return render_template('reset.html', error='Identifier is required')

        user = session.query(User).filter(
            (User.username == data['identifier']) |
            (User.email == data['identifier']) |
            (User.phone == data['identifier'])
        ).first()

        if user is None:
            return render_template('reset.html', error='User not found')

        user.generate_reset_token()
        session.commit()

        return render_template('reset.html', message='Password reset token generated', reset_token=user.reset_token)

    return render_template('reset.html')


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    """
    Route to reset the password.
    Expects a JSON payload with reset_token and new_password.
    """
    if request.method == 'POST':
        data = request.get_json() or request.form

        # Validate request data
        if not all(key in data for key in ('reset_token', 'new_password')):
            return render_template('reset.html', error='Reset token and new password are required')

        user = session.query(User).filter_by(reset_token=data['reset_token']).first()

        if user is None:
            return render_template('reset.html', error='Invalid reset token')

        user.set_password(data['new_password'])
        user.reset_token = None
        session.commit()

        return render_template('reset.html', message='Password reset successful')

    return render_template('reset.html')


@app.route('/help')
def help():
    """
    Route to render the help page.
    """
    return render_template('help.html')


@app.route('/helps_p_r', methods=['POST'])
def add_guide_pilarium():
    """
    Route to add a new guide for "Raid Shadow Legends".
    Expects a JSON payload with content, link, video, and image.
    """
    data = request.get_json()

    # Validate request data
    if not all(key in data for key in ('content', 'link', 'video', 'image')):
        return jsonify({'error': 'Content, link, video, and image are required'}), 400

    game_name = ""
    game = session.query(Game).filter_by(name=game_name).first()
    if not game:
        return jsonify({'error': f'Game {game_name} not found'}), 404

    new_guide = PilariumGuide(content=data['content'], link=data['link'], video=data['video'], image=data['image'])
    game.guides.append(new_guide)
    session.add(new_guide)
    session.commit()

    return render_template('help_raid_sl_request.html', message='New guide added successfully for Raid Shadow Legends'), 201


@app.route('/help_o_r', methods=['POST'])
def add_guide_all_games():
    """
    Route to add a new guide for any game.
    Expects a JSON payload with game_name, content, link, video, and image.
    """
    data = request.get_json()

    # Validate request data
    if not all(key in data for key in ('game_name', 'content', 'link', 'video', 'image')):
        return jsonify({'error': 'Game name, content, link, video, and image are required'}), 400

    game = session.query(Game).filter_by(name=data['game_name']).first()
    if not game:
        return jsonify({'error': f'Game {data["game_name"]} not found'}), 404

    new_guide = Guide(content=data['content'], link=data['link'], video=data['video'], image=data['image'], game_id=game.id)
    game.guides.append(new_guide)
    session.add(new_guide)
    session.commit()

    return render_template('help_request_onother.html', message=f'New guide added successfully for game {data["game_name"]}'), 201


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


@app.route('/edit_guide/<int:guide_id>', methods=['PUT'])
@login_required
def edit_guide(guide_id):
    """
    Route to edit an existing guide.
    Expects a JSON payload with optional fields: content, link, video, image.
    """
    data = request.get_json()
    guide = session.query(Guide).get(guide_id)

    if not guide:
        return jsonify({'error': 'Guide not found'}), 404

    if 'content' in data:
        guide.content = data['content']
    if 'link' in data:
        guide.link = data['link']
    if 'video' in data:
        guide.video = data['video']
    if 'image' in data:
        guide.image = data['image']

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return jsonify({'error': 'An error occurred while updating the guide'}), 400

    guides = session.query(Guide).all()
    return render_template('helps_manager.html', guides=guides, message='Guide updated successfully'), 200


@app.route('/edit_pilarium_guide/<int:guide_id>', methods=['PUT'])
@login_required
def edit_pilarium_guide(guide_id):
    """
    Route to edit an existing Pilarium guide.
    Expects a JSON payload with optional fields: content, link, video, image.
    """
    data = request.get_json()
    guide = session.query(PilariumGuide).get(guide_id)

    if not guide:
        return jsonify({'error': 'Guide not found'}), 404

    if 'content' in data:
        guide.content = data['content']
    if 'link' in data:
        guide.link = data['link']
    if 'video' in data:
        guide.video = data['video']
    if 'image' in data:
        guide.image = data['image']

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return jsonify({'error': 'An error occurred while updating the guide'}), 400

    pilarium_guides = session.query(PilariumGuide).all()
    return render_template('helps_manager.html', pilarium_guides=pilarium_guides, message='Pilarium guide updated successfully'), 200
