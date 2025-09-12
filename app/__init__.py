import logging

from app.lib.context_processor import cookie_preference, now_iso_8601, now_timestamp
from app.lib.limiter import limiter
from app.lib.talisman import talisman
from app.lib.template_filters import slugify
from flask import Flask, render_template
from flask_cors import CORS
from flask_session import Session
from jinja2 import ChoiceLoader, PackageLoader
from tna_frontend_jinja.wtforms.helpers import WTFormsHelpers


def create_app(config_class):
    app = Flask(__name__, static_url_path="/forms/static")
    app.config.from_object(config_class)

    gunicorn_error_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers.extend(gunicorn_error_logger.handlers)
    app.logger.setLevel(gunicorn_error_logger.level or "DEBUG")

    csp_self = "'self'"
    csp_none = "'none'"
    default_csp = csp_self
    csp_rules = {
        key.replace("_", "-"): value
        for key, value in app.config.get_namespace(
            "CSP_", lowercase=True, trim_namespace=True
        ).items()
        if not key.startswith("feature_") and value not in [None, [default_csp]]
    }
    talisman.init_app(
        app,
        content_security_policy={
            "default-src": default_csp,
            "base-uri": csp_none,
            "object-src": csp_none,
        }
        | csp_rules,
        feature_policy={
            "fullscreen": app.config.get("CSP_FEATURE_FULLSCREEN", csp_self),
            "picture-in-picture": app.config.get(
                "CSP_FEATURE_PICTURE_IN_PICTURE", csp_self
            ),
        },
        force_https=app.config["FORCE_HTTPS"],
    )

    limiter.init_app(app)

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return render_template("errors/rate.html"), 429

    @app.after_request
    def apply_extra_headers(response):
        if "X-Permitted-Cross-Domain-Policies" not in response.headers:
            response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        if "Cross-Origin-Embedder-Policy" not in response.headers:
            response.headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
        if "Cross-Origin-Opener-Policy" not in response.headers:
            response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        if "Cross-Origin-Resource-Policy" not in response.headers:
            response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        return response

    CORS(app)

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    app.jinja_loader = ChoiceLoader(
        [
            PackageLoader("app"),
            PackageLoader("tna_frontend_jinja"),
        ]
    )

    WTFormsHelpers(app)

    if app.config.get("SESSION_TYPE") and app.config.get("SESSION_REDIS"):
        Session(app)

    app.add_template_filter(slugify)

    @app.context_processor
    def context_processor():
        return dict(
            cookie_preference=cookie_preference,
            now_iso_8601=now_iso_8601,
            now_timestamp=now_timestamp,
            app_config={
                "ENVIRONMENT_NAME": app.config.get("ENVIRONMENT_NAME"),
                "CONTAINER_IMAGE": app.config.get("CONTAINER_IMAGE"),
                "BUILD_VERSION": app.config.get("BUILD_VERSION"),
                "TNA_FRONTEND_VERSION": app.config.get("TNA_FRONTEND_VERSION"),
                "COOKIE_DOMAIN": app.config.get("COOKIE_DOMAIN"),
                "GA4_ID": app.config.get("GA4_ID"),
            },
            feature={},
        )

    from .altcha import bp as altcha_bp
    from .forms import bp as forms_bp
    from .healthcheck import bp as healthcheck_bp
    from .main import bp as site_bp

    app.register_blueprint(site_bp)
    app.register_blueprint(healthcheck_bp, url_prefix="/healthcheck")
    app.register_blueprint(altcha_bp, url_prefix="/altcha")
    app.register_blueprint(forms_bp)

    return app
