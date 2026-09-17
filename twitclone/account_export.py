"""User-controlled, provider-neutral portable data export."""

from datetime import UTC

from twitclone.models import Quote, Tweet
from twitclone.reply_models import Reply
from twitclone.resource_models import Resource, ResourceRevision
from twitclone.spaces.models import SpaceMembership


def _iso(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _removal(item):
    return {
        "is_removed": item.is_removed,
        "removed_at": _iso(item.removed_at),
        "removal_reason": item.removal_reason,
    }


def build_portable_export(user, *, exported_at):
    """Return the first stable Ripple portability document for ``user``.

    This intentionally covers account identity, social connections, and authored
    public content. Private messages, moderation records, billing records,
    analytics, media bytes, and authentication secrets are outside v1.
    """

    posts = Tweet.query.filter_by(user_id=user.id).order_by(Tweet.id.asc()).all()
    quotes = Quote.query.filter_by(user_id=user.id).order_by(Quote.id.asc()).all()
    replies = Reply.query.filter_by(user_id=user.id).order_by(Reply.id.asc()).all()
    resources = Resource.query.filter_by(owner_id=user.id).order_by(Resource.id.asc()).all()
    memberships = SpaceMembership.query.filter_by(user_id=user.id).order_by(SpaceMembership.id.asc()).all()

    return {
        "format": "ripple-portable-export",
        "version": 1,
        "exported_at": _iso(exported_at),
        "scope": "account-profile-social-graph-and-authored-public-content",
        "account": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "bio": user.bio,
            "profile_theme": user.profile_theme,
            "profile_banner": user.profile_banner,
            "identity_verified": user.identity_verified,
            "verification_type": user.verification_type,
            "verified_at": _iso(user.verified_at),
        },
        "social_graph": {
            "following": sorted(item.username for item in user.followed.all()),
            "followers": sorted(item.username for item in user.followers.all()),
        },
        "posts": [
            {
                "id": item.id,
                "content": item.content,
                "created_at": _iso(item.timestamp),
                "image_reference": item.image,
                "original_image_reference": item.original_image,
                "scheduled_at": _iso(item.scheduled_at),
                **_removal(item),
            }
            for item in posts
        ],
        "quotes": [
            {
                "id": item.id,
                "root_post_id": item.tweet_id,
                "content": item.content,
                "created_at": _iso(item.timestamp),
                **_removal(item),
            }
            for item in quotes
        ],
        "replies": [
            {
                "id": item.id,
                "root_post_id": item.tweet_id,
                "parent_reply_id": item.parent_reply_id,
                "content": item.content,
                "created_at": _iso(item.created_at),
                **_removal(item),
            }
            for item in replies
        ],
        "resources": [
            {
                "id": item.id,
                "title": item.title,
                "created_at": _iso(item.created_at),
                "updated_at": _iso(item.updated_at),
                **_removal(item),
                "revisions": [
                    {
                        "id": revision.id,
                        "revision_number": revision.revision_number,
                        "body": revision.body,
                        "source_url": revision.source_url,
                        "change_note": revision.change_note,
                        "created_at": _iso(revision.created_at),
                    }
                    for revision in ResourceRevision.query.filter_by(resource_id=item.id)
                    .order_by(ResourceRevision.revision_number.asc())
                    .all()
                ],
            }
            for item in resources
        ],
        "space_memberships": [
            {
                "space_id": item.space_id,
                "space_slug": item.space.slug,
                "role": item.role,
                "joined_at": _iso(item.joined_at),
            }
            for item in memberships
        ],
        "not_included": [
            "authentication_secrets",
            "private_messages",
            "billing_records",
            "moderation_records",
            "analytics",
            "media_file_bytes",
        ],
    }


__all__ = ["build_portable_export"]
