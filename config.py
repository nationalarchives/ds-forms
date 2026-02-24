import json
import os

from app.lib.util import strtobool
from redis import Redis


class Features:
    pass


class Production(Features):
    CONTAINER_IMAGE: str = os.environ.get("CONTAINER_IMAGE", "")
    BUILD_VERSION: str = os.environ.get("BUILD_VERSION", "")
    TNA_FRONTEND_VERSION: str = ""
    try:
        with open(
            os.path.join(
                os.path.realpath(os.path.dirname(__file__)),
                "node_modules/@nationalarchives/frontend",
                "package.json",
            )
        ) as package_json:
            try:
                data = json.load(package_json)
                TNA_FRONTEND_VERSION = data["version"] or ""
            except ValueError:
                pass
    except FileNotFoundError:
        pass

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "")

    DEBUG: bool = False

    COOKIE_DOMAIN: str = os.environ.get("COOKIE_DOMAIN", "")

    CSP_IMG_SRC: list[str] = os.environ.get("CSP_IMG_SRC", "'self'").split(",")
    CSP_SCRIPT_SRC: list[str] = os.environ.get("CSP_SCRIPT_SRC", "'self'").split(",")
    CSP_STYLE_SRC: list[str] = os.environ.get("CSP_STYLE_SRC", "'self'").split(",")
    CSP_FONT_SRC: list[str] = os.environ.get("CSP_FONT_SRC", "'self'").split(",")
    CSP_CONNECT_SRC: list[str] = os.environ.get("CSP_CONNECT_SRC", "'self'").split(",")
    CSP_MEDIA_SRC: list[str] = os.environ.get("CSP_MEDIA_SRC", "'self'").split(",")
    CSP_WORKER_SRC: list[str] = os.environ.get("CSP_WORKER_SRC", "'self',blob:,").split(
        ","
    )
    CSP_FRAME_SRC: list[str] = os.environ.get("CSP_FRAME_SRC", "'self'").split(",")
    CSP_FRAME_ANCESTORS: list[str] = os.environ.get(
        "CSP_FRAME_ANCESTORS", "'self'"
    ).split(",")
    CSP_REPORT_URL: str = os.environ.get("CSP_REPORT_URL", "")
    if CSP_REPORT_URL:
        CSP_REPORT_URL += f"&sentry_release={BUILD_VERSION}" if BUILD_VERSION else ""
    FORCE_HTTPS: bool = strtobool(os.getenv("FORCE_HTTPS", "False"))
    PREFERRED_URL_SCHEME: str = os.getenv("PREFERRED_URL_SCHEME", "https")

    SESSION_COOKIE_NAME: str = "ds_forms_session"
    SESSION_COOKIE_PATH: str = "/"
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_REDIS_URL: str = os.environ.get("SESSION_REDIS_URL", "")
    if SESSION_REDIS_URL:
        SESSION_TYPE: str = "redis"
        SESSION_REDIS = Redis.from_url(SESSION_REDIS_URL)

    ALTCHA_HMAC_KEY: str = os.getenv("ALTCHA_HMAC_KEY", "")

    CACHE_TYPE: str = os.environ.get("CACHE_TYPE", "FileSystemCache")
    CACHE_DEFAULT_TIMEOUT: int = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", "3600"))
    CACHE_IGNORE_ERRORS: bool = True
    CACHE_DIR: str = os.environ.get("CACHE_DIR", "/tmp")
    CACHE_REDIS_URL: str = os.environ.get("CACHE_REDIS_URL", "")

    AWS_REGION: str = os.environ.get("AWS_REGION", "eu-west-2")
    SES_DEFAULT_FROM_EMAIL: str = os.environ.get(
        "SES_FROM_EMAIL", "noreply@nationalarchives.gov.uk"
    )

    GA4_ID: str = os.environ.get("GA4_ID", "")


class Staging(Production):
    DEBUG: bool = strtobool(os.getenv("DEBUG", "False"))


class Develop(Production):
    DEBUG: bool = strtobool(os.getenv("DEBUG", "False"))

    SESSION_COOKIE_SECURE: bool = strtobool(os.getenv("SESSION_COOKIE_SECURE", "True"))


class Test(Production):
    ENVIRONMENT_NAME: str = "test"

    SECRET_KEY: str = "abc123"
    DEBUG: bool = True
    TESTING: bool = True
    EXPLAIN_TEMPLATE_LOADING: bool = True

    FORCE_HTTPS: bool = False
    PREFERRED_URL_SCHEME: str = "http"
