from altcha import (
    ChallengeOptions,
    create_challenge,
)
from flask import current_app, jsonify

from app.altcha import bp


@bp.route("/", methods=["GET"])
def get_altcha():
    challenge = create_challenge(
        ChallengeOptions(
            hmac_key=current_app.config.get("ALTCHA_HMAC_KEY", "secret-hmac-key"),
        )
    )
    return jsonify(challenge.__dict__)
