"""
This module starts a Flask web application.
"""

from db import Base, engine

from app import app


def initialize_database():
    """
    Create database tables if they do not exist.
    """
    # Create all tables that do not exist yet
    Base.metadata.create_all(engine)


initialize_database()

if __name__ == "__main__":
    app.run(debug=True)
