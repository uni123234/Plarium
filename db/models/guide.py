"""
This module defines the Guide model.
"""

from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import ForeignKey
from db.base import BaseModel


class Guide(BaseModel):
    """
    Represents a guide associated with a user and a game.
    """

    __tablename__ = "guides"

    title: Mapped[str] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    link: Mapped[str] = mapped_column(nullable=False)
    video: Mapped[str] = mapped_column(nullable=False)
    image: Mapped[str] = mapped_column(nullable=False)
    usage_count: Mapped[int] = mapped_column(default=0)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)

    game = relationship("Game", back_populates="guides")
