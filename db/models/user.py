"""
This module defines the User model.
"""

from sqlalchemy.orm import relationship, Mapped, mapped_column
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from db.base import BaseModel
import secrets


class User(BaseModel, UserMixin):
    """
    Represents a user in the system.
    """

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    guides = relationship("Guide", backref="author", lazy=True)

    def set_password(self, password: str) -> None:
        """
        Sets the user's password, storing the hashed version.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        Checks the user's password against the stored hash.
        """
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self) -> str:
        """
        Generates a token for password reset.
        """
        return secrets.token_urlsafe()
