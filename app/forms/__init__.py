from flask import Blueprint

bp = Blueprint("forms", __name__)

from app.forms import routes  # noqa: E402,F401
