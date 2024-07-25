from flask_login import UserMixin
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

engine = create_engine("sqlite:///helps.db")
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()


class User(Base, UserMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    guides = relationship("Guide", backref="author", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        return secrets.token_urlsafe()


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    guides = relationship("Guide", back_populates="game")


class Guide(Base):
    __tablename__ = "guides"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    link = Column(String, nullable=False)
    video = Column(String, nullable=False)
    image = Column(String, nullable=False)
    usage_count = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)

    game = relationship("Game", back_populates="guides")


Base.metadata.create_all(engine)
