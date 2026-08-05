from flask import request
from flask_caching import Cache

cache = Cache()


def path_cache_key_prefix():
    return request.base_url


def page_cache_key_prefix():
    keys = [
        request.url,
        request.cookies.get("theme", "system"),
    ]
    return "_".join(keys)
