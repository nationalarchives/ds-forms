from http.cookies import SimpleCookie
from unittest.mock import patch

import pytest
from flask import jsonify, request
from redis import Redis

from app import create_app
from config import Test as TestConfig


def test_proxy_fix_uses_configured_proxy_depth_for_scheme_and_host():
    class Config(TestConfig):
        PROXY_DEPTH = 2

    app = create_app(Config)

    @app.get("/proxy-test")
    def proxy_test():
        return jsonify(
            scheme=request.scheme,
            host=request.host,
        )

    response = app.test_client().get(
        "/proxy-test",
        headers={
            "X-Forwarded-Proto": "https, http",
            "X-Forwarded-Host": "trusted.example, proxy.example",
        },
    )

    assert response.json == {
        "scheme": "https",
        "host": "trusted.example",
    }


@pytest.mark.parametrize(
    ("secure", "debug", "force_https"),
    [
        (True, True, False),
        (True, False, False),
        (True, False, True),
        (False, True, False),
        (False, False, True),
    ],
)
def test_session_cookie_respects_configuration_behind_proxy(secure, debug, force_https):
    class Config(TestConfig):
        SESSION_TYPE = "redis"
        SESSION_REDIS = Redis()
        PROXY_DEPTH = 1
        SESSION_COOKIE_SECURE = secure
        DEBUG = debug
        FORCE_HTTPS = force_https

    app = create_app(Config)
    with patch.object(Config.SESSION_REDIS, "set") as redis_set:
        response = app.test_client().get(
            "/contact-us/make-a-records-and-research-enquiry/",
            headers={"X-Forwarded-Proto": "https", "X-Forwarded-Host": "localhost"},
        )

    assert response.status_code == 200
    redis_set.assert_called_once()
    cookie = SimpleCookie()
    cookie.load(response.headers["Set-Cookie"])
    session_cookie = cookie["ds_forms_session"]
    expected_secure = secure or (force_https and not debug)
    assert bool(session_cookie["secure"]) is expected_secure
    assert session_cookie["httponly"]
    assert session_cookie["samesite"] == "Lax"
