"""Read-only version 1 public API routes."""

from datetime import UTC, datetime

from flask import jsonify

from twitclone.api import api_blueprint
from twitclone.extensions import db
from twitclone.models import Tweet
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


@api_blueprint.get("")
@api_blueprint.get("/")
def api_index():
    return jsonify(
        {
            "name": "Ripple Public API",
            "version": "v1",
            "status": "read-only-preview",
            "documentation": "/api/v1/",
        }
    )


@api_blueprint.get("/posts/<int:tweet_id>")
def get_post(tweet_id):
    tweet = db.session.get(Tweet, tweet_id)
    now = _utcnow_naive()
    if tweet is None or tweet.is_removed or (tweet.scheduled_at is not None and tweet.scheduled_at > now):
        return _api_error(404, "post_not_found", "The requested public post was not found.")
    return jsonify({"data": _public_post(tweet)})


@api_blueprint.errorhandler(404)
def api_not_found(_error):
    return _api_error(404, "not_found", "The requested API resource was not found.")


@api_blueprint.errorhandler(405)
def api_method_not_allowed(_error):
    return _api_error(405, "method_not_allowed", "This API endpoint does not support that method.")
