"""
This module defines the Game model.
"""

from sqlalchemy.orm import relationship, Mapped, mapped_column
from db.base import BaseModel


class Game(BaseModel):
    """
    Represents a game in the system.
    """

    __tablename__ = "games"

    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    guides = relationship("Guide", back_populates="game")
