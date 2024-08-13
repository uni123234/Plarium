"""
Error handling routes for the application.

This module defines error handlers for various HTTP error codes.
"""

from flask import render_template
from . import app


@app.errorhandler(Exception)
def handle_error(error):
    """
    Handle various HTTP errors and log the error.

    Args:
        error (Exception): The exception instance containing error information.

    Returns:
        Rendered template of an error page with the appropriate HTTP status code.
    """
    # Log the error
    app.logger.error("Error occurred: %s", error)

    # Determine the error code and provide a suitable error message
    error_code = getattr(error, "code", 500)

    # Handle different error codes and return the corresponding error page
    if error_code == 404:
        return render_template("error.html", message="Page not found"), 404
    elif error_code == 403:
        return render_template("error.html", message="Forbidden access"), 403
    elif error_code == 415:
        return render_template("error.html", message="Unsupported media type"), 415
    else:
        return render_template("error.html", message="Internal server error"), 500
