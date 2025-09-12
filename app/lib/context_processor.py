import json
from datetime import datetime
from urllib.parse import unquote

from flask import request


def now_iso_8601():
    now = datetime.now()
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def now_timestamp():
    now = datetime.now()
    return now.timestamp()


def cookie_preference(policy):
    if "cookies_policy" in request.cookies:
        cookies_policy = request.cookies["cookies_policy"]
        preferences = json.loads(unquote(cookies_policy))
        return preferences[policy] if policy in preferences else None
    return None
