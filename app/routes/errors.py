from flask import redirect, url_for
from . import app


@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(415)
@app.errorhandler(500)
def not_found(massage):
    app.logger.error(f"{massage}")
    return redirect(url_for("index"))