from flask import Blueprint

bp = Blueprint("altcha", __name__)

from app.altcha import routes  # noqa: E402,F401
