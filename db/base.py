# db/base.py

from sqlalchemy import create_engine, Integer
from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column


Base = declarative_base()


class BaseModel(Base):
    """
    A base model class that includes common columns.
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True)


engine = create_engine("sqlite:///helps.db")
Session = sessionmaker(bind=engine)
session = Session()
