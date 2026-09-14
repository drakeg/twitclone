"""Version 1 public API routes."""

from datetime import UTC, datetime

from flask import jsonify, request

from twitclone.api import api_blueprint
from twitclone.api.credentials import authenticate_bearer_token
from twitclone.extensions import db
from twitclone.models import Tweet
from twitclone.spaces.models import SpacePost
from twitclone.topic_models import public_topic_associations


def _utcnow_naive():
    return datetime.now(UTC).replace(tzinfo=None)


def _api_error(status_code, code, message):
    response = jsonify({"error": {"code": code, "message": message}})
    response.status_code = status_code
    return response


def _public_post(tweet):
    topics = [
        {"name": association.topic.name, "slug": association.topic.slug, "source": association.source}
        for association in public_topic_associations(tweet)
    ]
    return {
        "id": tweet.id,
        "type": "post",
        "content": tweet.content,
        "author": {"id": tweet.user.id, "username": tweet.user.username},
        "published_at": (tweet.scheduled_at or tweet.timestamp).isoformat() + "Z",
        "topics": topics,
        "url": f"/post/{tweet.id}",
    }


def _is_public_post(tweet, now):
    if tweet is None or tweet.is_removed:
        return False
    if tweet.scheduled_at is not None and tweet.scheduled_at > now:
        return False
    return SpacePost.query.filter_by(tweet_id=tweet.id).first() is None


def _bearer_credential(required_scope):
    authorization = request.headers.get("Authorization", "")
    scheme, separator, raw_token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not raw_token.strip():
        return None, _api_error(401, "invalid_token", "A valid bearer token is required.")

    credential = authenticate_bearer_token(raw_token.strip())
    if credential is None:
        return None, _api_error(401, "invalid_token", "The bearer token is invalid, expired, or revoked.")
    if required_scope not in credential.scope_set:
        return None, _api_error(403, "insufficient_scope", f"This operation requires the {required_scope} scope.")
    return credential, None


@api_blueprint.get("")
@api_blueprint.get("/")
def api_index():
    return jsonify(
        {
            "name": "Ripple Public API",
            "version": "v1",
            "status": "read-only-preview",
            "documentation": "/api/v1/",
            "authentication": {
                "scheme": "Bearer",
                "supported_scopes": ["posts:read"],
            },
        }
    )


@api_blueprint.get("/posts/<int:tweet_id>")
def get_post(tweet_id):
    tweet = db.session.get(Tweet, tweet_id)
    if not _is_public_post(tweet, _utcnow_naive()):
        return _api_error(404, "post_not_found", "The requested public post was not found.")
    return jsonify({"data": _public_post(tweet)})


@api_blueprint.get("/account")
def api_account():
    credential, error = _bearer_credential("posts:read")
    if error is not None:
        return error
    return jsonify(
        {
            "data": {
                "user": {"id": credential.user.id, "username": credential.user.username},
                "credential": {
                    "id": credential.id,
                    "label": credential.label,
                    "token_prefix": credential.token_prefix,
                    "scopes": sorted(credential.scope_set),
                    "expires_at": credential.expires_at.isoformat() + "Z" if credential.expires_at else None,
                },
            }
        }
    )


@api_blueprint.errorhandler(404)
def api_not_found(_error):
    return _api_error(404, "not_found", "The requested API resource was not found.")


@api_blueprint.errorhandler(405)
def api_method_not_allowed(_error):
    return _api_error(405, "method_not_allowed", "This API endpoint does not support that method.")
