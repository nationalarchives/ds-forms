import json
import os

from redis import Redis

from app.lib.util import strtobool


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
                # Can't get the version of TNA Frontend
                pass
    except FileNotFoundError:
        # Can't find the package.json file
        pass

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "")

    DEBUG: bool = False

    COOKIE_DOMAIN: str = os.environ.get("COOKIE_DOMAIN", ".nationalarchives.gov.uk")
    COOKIE_PREFERENCES_URL: str = os.environ.get("COOKIE_PREFERENCES_URL", "/cookies/")

    CSP_REPORT_URI: str = os.environ.get("CSP_REPORT_URI", "")
    if CSP_REPORT_URI and BUILD_VERSION:
        CSP_REPORT_URI += f"&sentry_release={BUILD_VERSION}" if BUILD_VERSION else ""
    CONTENT_SECURITY_POLICY: dict = {
        "connect-src": os.environ.get("CSP_CONNECT_SRC", "").split(","),
        "font-src": os.environ.get("CSP_FONT_SRC", "").split(","),
        "frame-ancestors": os.environ.get("CSP_FRAME_ANCESTORS", "").split(","),
        "frame-src": os.environ.get("CSP_FRAME_SRC", "").split(","),
        "img-src": os.environ.get("CSP_IMG_SRC", "").split(","),
        "media-src": os.environ.get("CSP_MEDIA_SRC", "").split(","),
        "report-uri": CSP_REPORT_URI,
        "script-src": os.environ.get("CSP_SCRIPT_SRC", "").split(","),
        "style-src": os.environ.get("CSP_STYLE_SRC", "").split(","),
        "worker-src": os.environ.get("CSP_WORKER_SRC", "").split(","),
    }
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
