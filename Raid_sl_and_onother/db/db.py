from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

Base = declarative_base()
engine = create_engine('sqlite:///helps.db')
Session = sessionmaker(bind=engine)
session = Session()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    phone = Column(String(15), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    reset_token = Column(String(200), nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe()

class Game(Base):
    __tablename__ = 'games'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(220), nullable=False)
    guides = relationship('Guide', back_populates='game')

class Guide(Base):
    __tablename__ = 'guides'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=True)
    link = Column(String(500), nullable=True)
    video = Column(String(500), nullable=True)
    image = Column(String(500), nullable=True)
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False)
    usage_count = Column(Integer, default=0) 
    game = relationship('Game', back_populates='guides')

class PilariumGuide(Base):
    __tablename__ = 'pilarium_guides'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=True)
    link = Column(String(500), nullable=True)
    video = Column(String(500), nullable=True)
    image = Column(String(500), nullable=True)
    usage_count = Column(Integer, default=0) 

Base.metadata.create_all(engine)

def register_user(username, email, phone, password):
    existing_user = session.query(User).filter((User.username == username) | (User.email == email) | (User.phone == phone)).first()
    if existing_user:
        return False 
    
    new_user = User(username=username, email=email, phone=phone)
    new_user.set_password(password)
    session.add(new_user)
    session.commit()
    return True  

def authenticate_user(identifier, password):
    user = session.query(User).filter((User.username == identifier) | (User.email == identifier) | (User.phone == identifier)).first()
    if user and user.check_password(password):
        return user 
    return None 

def generate_reset_token(identifier):
    user = session.query(User).filter((User.username == identifier) | (User.email == identifier) | (User.phone == identifier)).first()
    if user:
        user.generate_reset_token()
        session.commit()
        return user.reset_token
    return None 

