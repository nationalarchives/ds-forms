import json
import os
from typing import ClassVar

from flask import current_app
from redis import Redis

from app.lib.util import strtobool


class Features:
    pass


class Production(Features):
    for key in ["SECRET_KEY", "ALTCHA_HMAC_KEY", "ROSETTA_API_URL"]:
        if key not in os.environ:
            raise OSError(f"{key} not set")

    ENVIRONMENT_NAME: str = os.getenv("ENVIRONMENT_NAME", "production")
    BUILD_VERSION: str = os.getenv("BUILD_VERSION", "")
    CONTAINER_IMAGE: str = os.getenv("CONTAINER_IMAGE", "")
    TNA_FRONTEND_VERSION: str = ""
    try:
        package_lock_json_path = os.path.join(
            os.path.realpath(os.path.dirname(__file__)),
            "package-lock.json",
        )
        with open(package_lock_json_path) as package_json:
            data = json.load(package_json)
            TNA_FRONTEND_VERSION: str = (
                data.get("packages", {})
                .get("node_modules/@nationalarchives/frontend", {})
                .get("version", "")
            )
    except Exception:
        current_app.logger.exception("Error reading the version of TNA Frontend")

    SECRET_KEY: str = os.getenv("SECRET_KEY")

    DEBUG: bool = False

    COOKIE_DOMAIN: str = os.getenv("COOKIE_DOMAIN", ".nationalarchives.gov.uk")
    COOKIE_PREFERENCES_URL: str = os.getenv("COOKIE_PREFERENCES_URL", "/cookies/")

    CSP_REPORT_URI: str = os.getenv("CSP_REPORT_URI", "")
    if CSP_REPORT_URI and BUILD_VERSION:
        CSP_REPORT_URI += f"&sentry_release={BUILD_VERSION}" if BUILD_VERSION else ""
    CONTENT_SECURITY_POLICY: ClassVar[dict] = {
        "connect-src": os.getenv("CSP_CONNECT_SRC", "").split(","),
        "font-src": os.getenv("CSP_FONT_SRC", "").split(","),
        "frame-ancestors": os.getenv("CSP_FRAME_ANCESTORS", "").split(","),
        "frame-src": os.getenv("CSP_FRAME_SRC", "").split(","),
        "img-src": os.getenv("CSP_IMG_SRC", "").split(","),
        "media-src": os.getenv("CSP_MEDIA_SRC", "").split(","),
        "report-uri": CSP_REPORT_URI,
        "script-src": os.getenv("CSP_SCRIPT_SRC", "").split(","),
        "style-src": os.getenv("CSP_STYLE_SRC", "").split(","),
        "worker-src": os.getenv("CSP_WORKER_SRC", "'self',blob:").split(","),
    }
    FORCE_HTTPS: bool = strtobool(os.getenv("FORCE_HTTPS", "False"))
    PREFERRED_URL_SCHEME: str = os.getenv("PREFERRED_URL_SCHEME", "https")

    SESSION_COOKIE_NAME: str = "ds_forms_session"
    SESSION_COOKIE_PATH: str = "/"
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_REDIS_URL: str = os.getenv("SESSION_REDIS_URL", "")
    if SESSION_REDIS_URL:
        SESSION_TYPE: str = "redis"
        SESSION_REDIS = Redis.from_url(SESSION_REDIS_URL)

    ALTCHA_HMAC_KEY: str = os.getenv("ALTCHA_HMAC_KEY")

    CACHE_TYPE: str = os.getenv("CACHE_TYPE", "FileSystemCache")
    CACHE_DEFAULT_TIMEOUT: int = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "3600"))
    CACHE_IGNORE_ERRORS: bool = True
    CACHE_DIR: str = os.getenv("CACHE_DIR", "/tmp")
    CACHE_REDIS_URL: str = os.getenv("CACHE_REDIS_URL", "")

    DEFAULT_MINIMUM_TIME_TO_COMPLETE: int = int(
        os.getenv("DEFAULT_MINIMUM_TIME_TO_COMPLETE", "0")
    )

    AWS_REGION: str = os.getenv("AWS_REGION", "eu-west-2")
    SES_ENDPOINT: str = os.getenv("SES_ENDPOINT", None)
    DEFAULT_FROM_EMAIL: str = os.getenv(
        "SES_FROM_EMAIL", "noreply@nationalarchives.gov.uk"
    )

    DYNAMICS_ENTRA_ORG_URL: str = os.getenv("DYNAMICS_ENTRA_ORG_URL", "")
    DYNAMICS_ENTRA_TENANT_ID: str = os.getenv("DYNAMICS_ENTRA_TENANT_ID", "")
    DYNAMICS_ENTRA_CLIENT_ID: str = os.getenv("DYNAMICS_ENTRA_CLIENT_ID", "")
    DYNAMICS_ENTRA_CLIENT_SECRET: str = os.getenv("DYNAMICS_ENTRA_CLIENT_SECRET", "")
    DYNAMICS_ENTRA_SCOPE: str = os.getenv("DYNAMICS_ENTRA_SCOPE", "")

    DEFAULT_INBOX: str = os.getenv("DEFAULT_INBOX", "webmaster@nationalarchives.gov.uk")
    FORM_APPLY_TO_FILM_INBOX: str = os.getenv("FORM_APPLY_TO_FILM_INBOX", DEFAULT_INBOX)
    FORM_DISCOVERY_API_KEY_INBOX: str = os.getenv(
        "FORM_DISCOVERY_API_KEY_INBOX", DEFAULT_INBOX
    )
    FORM_HOLOCAUST_MEMORIAL_FOUNDATION_TESTIMONY_LICENCE_REQUEST_INBOX: str = os.getenv(
        "FORM_HOLOCAUST_MEMORIAL_FOUNDATION_TESTIMONY_LICENCE_REQUEST_INBOX",
        DEFAULT_INBOX,
    )
    FORM_RECORDS_ENQUIRY_INBOX: str = os.getenv(
        "FORM_RECORDS_ENQUIRY_INBOX", DEFAULT_INBOX
    )
    FORM_REPORT_A_CATALOGUE_ISSUE_INBOXES: str = {
        "DIGITAL_DOWNLOADS": os.getenv(
            "FORM_REPORT_A_CATALOGUE_ISSUE_DIGITAL_DOWNLOADS_INBOX", DEFAULT_INBOX
        ),
        "DIGITAL_PRESERVATION": os.getenv(
            "FORM_REPORT_A_CATALOGUE_ISSUE_DIGITAL_PRESERVATION_INBOX", DEFAULT_INBOX
        ),
        "FINDING_ARCHIVES_PROJECT": os.getenv(
            "FORM_REPORT_A_CATALOGUE_ISSUE_FINDING_ARCHIVES_PROJECT_INBOX",
            DEFAULT_INBOX,
        ),
        "CATALOGUE_AMENDMENTS": os.getenv(
            "FORM_REPORT_A_CATALOGUE_ISSUE_CATALOGUE_AMENDMENTS_INBOX", DEFAULT_INBOX
        ),
    }

    GA4_ID: str = os.getenv("GA4_ID", "")

    ROSETTA_API_URL: str = os.getenv("ROSETTA_API_URL")


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

    DEFAULT_MINIMUM_TIME_TO_COMPLETE: int = 0
