import unittest
from flask import json, url_for
from .config import app, db_session, User, Game, Guide
from ...db.db import Base, engine


class FlaskAppTests(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        app.config["SERVER_NAME"] = "a"
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        Base.metadata.create_all(engine)

    def tearDown(self):
        Base.metadata.drop_all(engine)
        self.app_context.pop()

    def test_index(self):
        response = self.app.get(url_for("index"))
        self.assertEqual(response.status_code, 200)

    def test_register(self):
        response = self.app.post(
            url_for("register"),
            data={
                "username": "testuser",
                "email": "testuser@example.com",
                "phone": "+1234567890",
                "password": "password",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"User registered successfully", response.data)

        user = db_session.query(User).filter_by(username="testuser").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "testuser@example.com")

    def test_login(self):
        user = User(
            username="testuser", email="testuser@example.com", phone="1234567890"
        )
        user.set_password("password")
        db_session.add(user)
        db_session.commit()

        response = self.app.post(
            url_for("login"), data={"identifier": "testuser", "password": "password"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/", response.location)

    def test_logout(self):
        self.test_login()
        response = self.app.get(url_for("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/", response.location)

    def test_add_game(self):
        self.test_login()
        response = self.app.post(url_for("add_game"), data={"game_name": "Test Game"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"New game added successfully", response.data)

        game = db_session.query(Game).filter_by(name="Test Game").first()
        self.assertIsNotNone(game)

    def test_edit_user(self):
        self.test_login()
        response = self.app.post(
            url_for("edit_user"),
            content_type="application/json",
            data=json.dumps(
                {
                    "username": "newusername",
                    "email": "newemail@example.com",
                }
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"User updated successfully", response.data)

        user = db_session.query(User).filter_by(username="newusername").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "newemail@example.com")

    def test_add_guide_all_games(self):
        self.test_login()
        game = Game(name="Test Game")
        db_session.add(game)
        db_session.commit()

        response = self.app.post(
            url_for("add_guide_all_games"),
            data={
                "game_name": "Test Game",
                "title": "Test Guide",
                "content": "This is a test guide.",
                "link": "http://example.com",
                "video": "http://example.com/video",
                "image": "http://example.com/image",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn(b"New guide added successfully for game Test Game", response.data)

        guide = db_session.query(Guide).filter_by(title="Test Guide").first()
        self.assertIsNotNone(guide)
        self.assertEqual(guide.content, "This is a test guide.")
