from flask import current_app

from app.healthcheck import bp
from app.lib.limiter import limiter


@bp.route("/live/")
@limiter.exempt
def healthcheck():
    return "ok"


@bp.route("/version/")
@limiter.exempt
def healthcheck_version():
    return current_app.config["BUILD_VERSION"]
