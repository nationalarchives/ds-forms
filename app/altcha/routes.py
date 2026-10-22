from altcha import create_challenge
from flask import current_app, jsonify

from app.altcha import bp


@bp.route("/", methods=["GET"])
def get_altcha():
    challenge = create_challenge(
        algorithm="PBKDF2/SHA-256",
        cost=5_000,
        hmac_secret=current_app.config.get("ALTCHA_HMAC_KEY", "secret-hmac-key"),
    )
    return jsonify(challenge.to_dict())
