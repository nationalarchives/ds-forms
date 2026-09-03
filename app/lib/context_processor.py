import json
from datetime import UTC, datetime
from urllib.parse import unquote

from flask import request


def now_iso_8601():
    now = datetime.now(UTC)
    return now.isoformat(timespec="seconds").replace("+00:00", "Z")


def now_timestamp():
    now = datetime.now(UTC)
    return now.timestamp()


def cookie_preference(policy):
    if "cookie_preferences" in request.cookies:
        cookie_preferences = request.cookies["cookie_preferences"]
        preferences = json.loads(unquote(cookie_preferences))
        return preferences.get(policy, None)
    return None
