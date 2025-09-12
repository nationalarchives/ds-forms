from app.healthcheck import bp
from app.lib.limiter import limiter


@bp.route("/live/")
@limiter.exempt
def healthcheck():
    return "ok"
