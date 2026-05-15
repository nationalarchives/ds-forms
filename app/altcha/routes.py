from altcha import (
    ChallengeOptions,
    create_challenge,
)
from flask import current_app, jsonify

from app.altcha import bp


@bp.route("/", methods=["GET"])
def get_altcha():
    try:
        challenge = create_challenge(
            ChallengeOptions(
                hmac_key=current_app.config.get("ALTCHA_HMAC_KEY", "secret-hmac-key"),
            )
        )
        return jsonify(challenge.__dict__)
    except Exception as e:
        return jsonify({"error": f"Failed to create challenge: {e!s}"}), 500
