"""Version 1 public API routes."""

from datetime import UTC, datetime

from flask import current_app, jsonify, request

from twitclone.api import api_blueprint
from twitclone.api.credentials import SUPPORTED_API_SCOPES, authenticate_bearer_token
from twitclone.api.rate_limits import (
    DEFAULT_CREDENTIAL_LIMIT,
    DEFAULT_INVALID_TOKEN_LIMIT,
    DEFAULT_PUBLIC_READ_LIMIT,
    DEFAULT_WINDOW_SECONDS,
    consume_rate_limit,
)
from twitclone.conversation_intent import normalize_conversation_intent
from twitclone.conversation_models import TweetConversationIntent
from twitclone.extensions import db
from twitclone.mentions import add_mention_notifications, mentioned_usernames
from twitclone.models import Tweet
from twitclone.spaces.models import SpacePost
from twitclone.timeline.validation import validate_post_content
from twitclone.topic_models import associate_topics, public_topic_associations, replace_explicit_topics


def _utcnow_naive():
    return datetime.now(UTC).replace(tzinfo=None)


def _api_error(status_code, code, message):
    response = jsonify({"error": {"code": code, "message": message}})
    response.status_code = status_code
    return response


def _limit_value(config_key, default):
    return int(current_app.config.get(config_key, default))


def _consume_limit(bucket_type, subject, config_key, default_limit):
    return consume_rate_limit(
        bucket_type=bucket_type,
        subject=subject,
        secret_key=current_app.config.get("SECRET_KEY", ""),
        limit=_limit_value(config_key, default_limit),
        window_seconds=_limit_value("API_RATE_LIMIT_WINDOW_SECONDS", DEFAULT_WINDOW_SECONDS),
    )


def _with_rate_limit_headers(response, result):
    response.headers["X-RateLimit-Limit"] = str(result.limit)
    response.headers["X-RateLimit-Remaining"] = str(result.remaining)
    response.headers["X-RateLimit-Reset"] = str(
        int(result.reset_at.replace(tzinfo=UTC).timestamp())
    )
    return response


def _rate_limited_response(result):
    response = _api_error(
        429,
        "rate_limited",
        "Request limit exceeded. Retry after the indicated interval.",
    )
    response.headers["Retry-After"] = str(result.retry_after)
    return _with_rate_limit_headers(response, result)


def _client_subject():
    return request.remote_addr or "unknown-client"


def _public_read_limit():
    result = _consume_limit(
        "public_read",
        _client_subject(),
        "API_PUBLIC_READ_LIMIT",
        DEFAULT_PUBLIC_READ_LIMIT,
    )
    if not result.allowed:
        return result, _rate_limited_response(result)
    return result, None


def _invalid_token_response(message):
    result = _consume_limit(
        "invalid_token",
        _client_subject(),
        "API_INVALID_TOKEN_LIMIT",
        DEFAULT_INVALID_TOKEN_LIMIT,
    )
    if not result.allowed:
        return _rate_limited_response(result)
    return _with_rate_limit_headers(_api_error(401, "invalid_token", message), result)


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
        "edited_at": tweet.edited_at.isoformat() + "Z" if tweet.edited_at else None,
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
        return None, _invalid_token_response("A valid bearer token is required."), None

    credential = authenticate_bearer_token(raw_token.strip())
    if credential is None:
        return None, _invalid_token_response(
            "The bearer token is invalid, expired, or revoked."
        ), None

    result = _consume_limit(
        "credential",
        str(credential.id),
        "API_CREDENTIAL_LIMIT",
        DEFAULT_CREDENTIAL_LIMIT,
    )
    if not result.allowed:
        return None, _rate_limited_response(result), result
    if required_scope not in credential.scope_set:
        response = _api_error(
            403,
            "insufficient_scope",
            f"This operation requires the {required_scope} scope.",
        )
        return None, _with_rate_limit_headers(response, result), result
    return credential, None, result


def _owned_mutable_post(tweet_id, credential):
    tweet = db.session.get(Tweet, tweet_id)
    if tweet is None:
        return None, _api_error(404, "post_not_found", "The requested post was not found.")
    if not _is_public_post(tweet, _utcnow_naive()):
        return None, _api_error(404, "post_not_found", "The requested mutable post was not found.")
    if tweet.user_id != credential.user_id:
        return None, _api_error(403, "post_not_owned", "The credential owner cannot modify this post.")
    return tweet, None


def _edit_payload_error(payload):
    if not isinstance(payload, dict):
        return "Request body must be a JSON object."
    if set(payload) != {"content"}:
        return "Edit requests accept only the content field."
    return validate_post_content(payload.get("content"), post_type="Post")


def _post_payload_error(payload):
    if not isinstance(payload, dict):
        return "Request body must be a JSON object."
    content = payload.get("content")
    validation_error = validate_post_content(content, post_type="Post")
    if validation_error:
        return validation_error
    topics = payload.get("topics", [])
    if topics is None:
        topics = []
    if not isinstance(topics, list) or len(topics) > 5 or not all(isinstance(item, str) for item in topics):
        return "topics must be an array of at most five strings."
    conversation_intent = payload.get("conversation_intent")
    if conversation_intent is not None and not isinstance(conversation_intent, str):
        return "conversation_intent must be a string when provided."
    return None


@api_blueprint.get("")
@api_blueprint.get("/")
def api_index():
    limit_result, error = _public_read_limit()
    if error is not None:
        return error
    response = jsonify(
        {
            "name": "Ripple Public API",
            "version": "v1",
            "status": "limited-write-preview",
            "documentation": "/api/v1/",
            "authentication": {
                "scheme": "Bearer",
                "supported_scopes": sorted(SUPPORTED_API_SCOPES),
            },
        }
    )
    return _with_rate_limit_headers(response, limit_result)


@api_blueprint.get("/posts/<int:tweet_id>")
def get_post(tweet_id):
    limit_result, error = _public_read_limit()
    if error is not None:
        return error
    tweet = db.session.get(Tweet, tweet_id)
    if not _is_public_post(tweet, _utcnow_naive()):
        return _with_rate_limit_headers(
            _api_error(404, "post_not_found", "The requested public post was not found."),
            limit_result,
        )
    return _with_rate_limit_headers(
        jsonify({"data": _public_post(tweet)}),
        limit_result,
    )


@api_blueprint.post("/posts")
def create_post():
    credential, error, limit_result = _bearer_credential("posts:write")
    if error is not None:
        return error

    payload = request.get_json(silent=True)
    payload_error = _post_payload_error(payload)
    if payload_error:
        return _with_rate_limit_headers(
            _api_error(400, "invalid_post", payload_error),
            limit_result,
        )

    content = payload["content"].strip()
    intent = normalize_conversation_intent(payload.get("conversation_intent"))
    topics = payload.get("topics") or []
    tweet = Tweet(content=content, user_id=credential.user_id)
    db.session.add(tweet)
    db.session.flush()
    db.session.add(TweetConversationIntent(tweet_id=tweet.id, intent=intent))
    associate_topics(tweet, explicit_raw=",".join(topics), content=content)
    add_mention_notifications(content=content, author=credential.user, tweet_id=tweet.id)
    db.session.commit()

    response = jsonify({"data": _public_post(tweet)})
    response.status_code = 201
    response.headers["Location"] = f"/api/v1/posts/{tweet.id}"
    return _with_rate_limit_headers(response, limit_result)


@api_blueprint.patch("/posts/<int:tweet_id>")
def edit_post(tweet_id):
    credential, error, limit_result = _bearer_credential("posts:write")
    if error is not None:
        return error

    tweet, ownership_error = _owned_mutable_post(tweet_id, credential)
    if ownership_error is not None:
        return _with_rate_limit_headers(ownership_error, limit_result)

    payload = request.get_json(silent=True)
    payload_error = _edit_payload_error(payload)
    if payload_error:
        return _with_rate_limit_headers(
            _api_error(400, "invalid_post", payload_error),
            limit_result,
        )

    content = payload["content"].strip()
    if content != tweet.content:
        previous_mentions = mentioned_usernames(tweet.content)
        current_mentions = mentioned_usernames(content)
        explicit_topics = ", ".join(
            row.topic.name
            for row in tweet.topic_associations
            if row.source == "explicit"
        )
        tweet.content = content
        replace_explicit_topics(tweet, explicit_topics)
        tweet.edited_at = _utcnow_naive()
        add_mention_notifications(
            content=content,
            author=credential.user,
            tweet_id=tweet.id,
            usernames=current_mentions - previous_mentions,
        )
        db.session.commit()

    return _with_rate_limit_headers(
        jsonify({"data": _public_post(tweet)}),
        limit_result,
    )


@api_blueprint.delete("/posts/<int:tweet_id>")
def remove_post(tweet_id):
    credential, error, limit_result = _bearer_credential("posts:write")
    if error is not None:
        return error

    tweet, ownership_error = _owned_mutable_post(tweet_id, credential)
    if ownership_error is not None:
        return _with_rate_limit_headers(ownership_error, limit_result)

    tweet.is_removed = True
    tweet.removed_at = _utcnow_naive()
    tweet.removed_by_id = credential.user_id
    tweet.removal_reason = "Removed by author."
    db.session.commit()

    response = current_app.response_class(status=204)
    return _with_rate_limit_headers(response, limit_result)


@api_blueprint.get("/account")
def api_account():
    credential, error, limit_result = _bearer_credential("posts:read")
    if error is not None:
        return error
    response = jsonify(
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
    return _with_rate_limit_headers(response, limit_result)


@api_blueprint.errorhandler(404)
def api_not_found(_error):
    return _api_error(404, "not_found", "The requested API resource was not found.")


@api_blueprint.errorhandler(405)
def api_method_not_allowed(_error):
    return _api_error(405, "method_not_allowed", "This API endpoint does not support that method.")
