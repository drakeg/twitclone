"""User-controlled, provider-neutral portable data export."""

from datetime import UTC

from sqlalchemy import and_, or_

from twitclone.models import DirectMessage, Entitlement, Quote, Subscription, Tweet
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

    This covers account identity, social connections, authored public content,
    and direct messages still visible to the requester. Moderation records,
    subscription/entitlement state, and an owned-media reference manifest.
    Analytics, media bytes, payment credentials, provider identifiers, and
    authentication secrets remain outside version 4.
    """

    posts = Tweet.query.filter_by(user_id=user.id).order_by(Tweet.id.asc()).all()
    quotes = Quote.query.filter_by(user_id=user.id).order_by(Quote.id.asc()).all()
    replies = Reply.query.filter_by(user_id=user.id).order_by(Reply.id.asc()).all()
    resources = Resource.query.filter_by(owner_id=user.id).order_by(Resource.id.asc()).all()
    memberships = SpaceMembership.query.filter_by(user_id=user.id).order_by(SpaceMembership.id.asc()).all()
    messages = (
        DirectMessage.query.filter(
            or_(
                and_(DirectMessage.sender_id == user.id, DirectMessage.deleted_by_sender.is_(False)),
                and_(DirectMessage.receiver_id == user.id, DirectMessage.deleted_by_receiver.is_(False)),
            )
        )
        .order_by(DirectMessage.timestamp.asc(), DirectMessage.id.asc())
        .all()
    )
    subscriptions = Subscription.query.filter_by(user_id=user.id).order_by(Subscription.id.asc()).all()
    entitlements = Entitlement.query.filter_by(user_id=user.id).order_by(Entitlement.id.asc()).all()

    return {
        "format": "ripple-portable-export",
        "version": 4,
        "exported_at": _iso(exported_at),
        "scope": "account-profile-social-graph-authored-content-visible-messages-billing-state-and-media-manifest",
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
        "private_messages": [
            {
                "id": item.id,
                "direction": "sent" if item.sender_id == user.id else "received",
                "participant": item.receiver.username if item.sender_id == user.id else item.sender.username,
                "content": item.content,
                "sent_at": _iso(item.timestamp),
            }
            for item in messages
        ],
        "subscriptions": [
            {
                "id": item.id,
                "plan": {
                    "key": item.plan.key,
                    "name": item.plan.name,
                    "catalog_amount_cents": item.plan.amount_cents,
                    "currency": item.plan.currency,
                    "interval": item.plan.interval,
                },
                "provider": item.provider,
                "status": item.status,
                "current_period_start": _iso(item.current_period_start),
                "current_period_end": _iso(item.current_period_end),
                "created_at": _iso(item.created_at),
                "updated_at": _iso(item.updated_at),
            }
            for item in subscriptions
        ],
        "entitlements": [
            {
                "id": item.id,
                "key": item.key,
                "active": item.active,
                "source": item.source,
                "subscription_id": item.subscription_id,
                "granted_at": _iso(item.granted_at),
                "expires_at": _iso(item.expires_at),
            }
            for item in entitlements
        ],
        "creator_support_transactions": {
            "status": "not_available",
            "reason": "Ripple does not currently process or persist creator-support transactions.",
        },
        "media_manifest": {
            "packaged_bytes": False,
            "assets": (
                ([{
                    "kind": "profile_banner",
                    "source_id": None,
                    "reference": user.profile_banner,
                }] if user.profile_banner else [])
                + [
                    {
                        "kind": "post_image",
                        "source_id": item.id,
                        "reference": item.image,
                    }
                    for item in posts
                    if item.image
                ]
                + [
                    {
                        "kind": "post_original_image",
                        "source_id": item.id,
                        "reference": item.original_image,
                    }
                    for item in posts
                    if item.original_image
                ]
            ),
        },
        "not_included": [
            "authentication_secrets",
            "payment_credentials",
            "provider_customer_and_subscription_identifiers",
            "invoices_and_charge_receipts",
            "moderation_records",
            "analytics",
            "media_file_bytes",
        ],
    }


__all__ = ["build_portable_export"]
