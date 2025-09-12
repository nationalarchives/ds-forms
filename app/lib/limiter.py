import os

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    get_remote_address,
    default_limits=os.environ.get("RATELIMIT_DEFAULT", "").split(","),
    storage_uri=os.environ.get("REDIS_URL", "memory://"),
    strategy="fixed-window",
)
