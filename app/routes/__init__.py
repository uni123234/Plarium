"""
Initialize logging and import route modules.

This module sets up logging for the application and imports the route modules
for error handling, default routes, authentication, and guides.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from ..config import app

# Define log file constants
LOG_DIRECTORY = "logs"
LOG_FILE_PATH = os.path.join(LOG_DIRECTORY, "application.log")

# Ensure the logs directory exists
if not os.path.exists(LOG_DIRECTORY):
    try:
        os.makedirs(LOG_DIRECTORY)
    except OSError as e:
        raise RuntimeError(f"Failed to create log directory: {e}") from e

# Set up the logging handler
handler = RotatingFileHandler(
    LOG_FILE_PATH, maxBytes=100000, backupCount=1
)  # Adjust maxBytes as needed
handler.setLevel(logging.INFO)  # Set to DEBUG for development

# Set up the logging format
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

# Add the handler to the app's logger
app.logger.addHandler(handler)
app.logger.setLevel(
    logging.INFO
)  # Ensure the app logger is set to the appropriate level

# Import route modules
from . import errors, default, auth, guide
