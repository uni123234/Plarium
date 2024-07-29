import logging, os
from logging.handlers import RotatingFileHandler
from ..config import (
    app,
)


if not os.path.exists("logs"):
    os.makedirs("logs")

handler = RotatingFileHandler("logs/application.log", maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
app.logger.addHandler(handler)


from . import errors, default, auth, guide