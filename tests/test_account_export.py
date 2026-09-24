"""Sprint 18 user-controlled portability coverage."""

from twitclone.extensions import db
from twitclone.models import DirectMessage, Entitlement, Follows, Plan, Quote, Subscription, Tweet, User
from twitclone.reply_models import Reply
from twitclone.resource_models import Resource, ResourceRevision
from twitclone.spaces.models import Space, SpaceMembership


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _seed_export(app):
    with app.app_context():
        owner = User(username="export_owner", email="owner@example.com", password="secret-hash", bio="Portable profile", profile_banner="owner-banner.png")
        follower = User(username="export_follower", email="follower@example.com", password="other-secret")
        outsider = User(username="export_outsider", email="outsider@example.com", password="outside-secret")
        db.session.add_all([owner, follower, outsider]); db.session.flush()
        db.session.add_all([
            Follows(follower_id=owner.id, followed_id=follower.id),
            Follows(follower_id=follower.id, followed_id=owner.id),
        ])
        owner_post = Tweet(
            content="Owner portable post",
            user_id=owner.id,
            image="owner-post.jpg",
            original_image="owner-post-original.jpg",
            edited_at=db.func.now(),
        )
        outsider_post = Tweet(content="Outsider private-to-export post", user_id=outsider.id, image="outsider-post.jpg")
        db.session.add_all([owner_post, outsider_post]); db.session.flush()
        db.session.add(Quote(content="Owner quote", user_id=owner.id, tweet_id=outsider_post.id))
        db.session.add(Reply(content="Owner reply", user_id=owner.id, tweet_id=outsider_post.id))
        removed = Tweet(content="Owner removed post", user_id=owner.id, is_removed=True, removal_reason="author record")
        db.session.add(removed)
        db.session.flush()
        removed.removed_by_id = owner.id
        resource = Resource(owner_id=owner.id, title="Owner guide")
        db.session.add(resource); db.session.flush()
        revision = ResourceRevision(resource_id=resource.id, editor_id=owner.id, revision_number=1, body="Portable knowledge")
        db.session.add(revision); db.session.flush(); resource.current_revision_id = revision.id
        space = Space(slug="portable-space", name="Portable Space", description="Export context", owner_id=owner.id)
        db.session.add(space); db.session.flush()
        db.session.add(SpaceMembership(space_id=space.id, user_id=owner.id, role="owner"))
        db.session.commit()
        return owner.id


def test_export_requires_authentication(client):
    response = client.get("/profile/export.json")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_export_is_private_download_with_stable_scope(client, app):
    owner_id = _seed_export(app); _login(client, owner_id)
    response = client.get("/profile/export.json")

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert 'attachment; filename="ripple-export-export_owner.json"' == response.headers["Content-Disposition"]
    payload = response.get_json()
    assert payload["format"] == "ripple-portable-export"
    assert payload["version"] == 6
    assert payload["account"]["email"] == "owner@example.com"
    assert payload["social_graph"] == {"following": ["export_follower"], "followers": ["export_follower"]}
    assert [item["content"] for item in payload["posts"]] == ["Owner portable post", "Owner removed post"]
    assert payload["posts"][0]["edited_at"] is not None
    assert payload["posts"][1]["is_removed"] is True
    assert payload["posts"][1]["removal_origin"] == "owner"
    assert [item["content"] for item in payload["quotes"]] == ["Owner quote"]
    assert [item["content"] for item in payload["replies"]] == ["Owner reply"]
    assert payload["resources"][0]["revisions"][0]["body"] == "Portable knowledge"
    assert payload["space_memberships"] == [
        {"space_id": payload["space_memberships"][0]["space_id"], "space_slug": "portable-space", "role": "owner", "joined_at": payload["space_memberships"][0]["joined_at"]}
    ]


def test_export_excludes_secrets_and_other_accounts_content(client, app):
    owner_id = _seed_export(app); _login(client, owner_id)
    text = client.get("/profile/export.json").get_data(as_text=True)

    assert "secret-hash" not in text
    assert "other-secret" not in text
    assert "outside-secret" not in text
    assert "Outsider private-to-export post" not in text
    assert "authentication_secrets" in text


def test_export_includes_only_messages_visible_to_requester(client, app):
    with app.app_context():
        owner = User(username="message_owner", email="message-owner@example.com", password="owner-secret")
        partner = User(username="message_partner", email="message-partner@example.com", password="partner-secret")
        outsider = User(username="message_outsider", email="message-outsider@example.com", password="outsider-secret")
        db.session.add_all([owner, partner, outsider]); db.session.flush()
        db.session.add_all([
            DirectMessage(content="visible sent", sender_id=owner.id, receiver_id=partner.id),
            DirectMessage(content="visible received", sender_id=partner.id, receiver_id=owner.id, read=True),
            DirectMessage(content="deleted sent", sender_id=owner.id, receiver_id=partner.id, deleted_by_sender=True),
            DirectMessage(content="deleted received", sender_id=partner.id, receiver_id=owner.id, deleted_by_receiver=True),
            DirectMessage(content="unrelated conversation", sender_id=partner.id, receiver_id=outsider.id),
        ])
        db.session.commit(); owner_id = owner.id

    _login(client, owner_id)
    payload = client.get("/profile/export.json").get_json()

    assert payload["private_messages"] == [
        {
            "id": payload["private_messages"][0]["id"],
            "direction": "sent",
            "participant": "message_partner",
            "content": "visible sent",
            "sent_at": payload["private_messages"][0]["sent_at"],
        },
        {
            "id": payload["private_messages"][1]["id"],
            "direction": "received",
            "participant": "message_partner",
            "content": "visible received",
            "sent_at": payload["private_messages"][1]["sent_at"],
        },
    ]
    exported_text = str(payload)
    assert "deleted sent" not in exported_text
    assert "deleted received" not in exported_text
    assert "unrelated conversation" not in exported_text
    assert "read" not in payload["private_messages"][1]
    assert "deleted_by_sender" not in exported_text
    assert "deleted_by_receiver" not in exported_text


def test_export_includes_billing_state_without_provider_identifiers(client, app):
    with app.app_context():
        owner = User(username="billing_owner", email="billing-owner@example.com", password="owner-secret")
        outsider = User(username="billing_outsider", email="billing-outsider@example.com", password="outsider-secret")
        plan = Plan(key="portable_monthly", name="Portable Monthly", description="Export test", amount_cents=799, currency="USD", interval="month", entitlement_key="portable")
        db.session.add_all([owner, outsider, plan]); db.session.flush()
        subscription = Subscription(
            user_id=owner.id,
            plan_id=plan.id,
            provider="stripe",
            provider_customer_id="cus_secret_owner",
            provider_subscription_id="sub_secret_owner",
            status="active",
        )
        outsider_subscription = Subscription(
            user_id=outsider.id,
            plan_id=plan.id,
            provider="stripe",
            provider_customer_id="cus_secret_outsider",
            provider_subscription_id="sub_secret_outsider",
            status="active",
        )
        db.session.add_all([subscription, outsider_subscription]); db.session.flush()
        db.session.add(Entitlement(user_id=owner.id, key="portable", source="subscription", subscription_id=subscription.id, active=True))
        db.session.commit(); owner_id = owner.id

    _login(client, owner_id)
    payload = client.get("/profile/export.json").get_json()

    assert payload["subscriptions"] == [{
        "id": payload["subscriptions"][0]["id"],
        "plan": {"key": "portable_monthly", "name": "Portable Monthly", "catalog_amount_cents": 799, "currency": "USD", "interval": "month"},
        "provider": "stripe",
        "status": "active",
        "current_period_start": None,
        "current_period_end": None,
        "created_at": payload["subscriptions"][0]["created_at"],
        "updated_at": payload["subscriptions"][0]["updated_at"],
    }]
    assert payload["entitlements"][0]["key"] == "portable"
    assert payload["entitlements"][0]["subscription_id"] == payload["subscriptions"][0]["id"]
    assert payload["creator_support_transactions"]["status"] == "not_available"
    exported_text = str(payload)
    assert "cus_secret_owner" not in exported_text
    assert "sub_secret_owner" not in exported_text
    assert "cus_secret_outsider" not in exported_text
    assert "sub_secret_outsider" not in exported_text
    assert "provider_customer_id" not in exported_text
    assert "provider_subscription_id" not in exported_text


def test_export_media_manifest_only_references_requesters_owned_media(client, app):
    owner_id = _seed_export(app); _login(client, owner_id)
    payload = client.get("/profile/export.json").get_json()

    assert payload["media_manifest"] == {
        "packaged_bytes": False,
        "assets": [
            {"kind": "profile_banner", "source_id": None, "reference": "owner-banner.png"},
            {"kind": "post_image", "source_id": payload["posts"][0]["id"], "reference": "owner-post.jpg"},
            {"kind": "post_original_image", "source_id": payload["posts"][0]["id"], "reference": "owner-post-original.jpg"},
        ],
    }
    exported_text = str(payload["media_manifest"])
    assert "outsider-post.jpg" not in exported_text
    assert "media_file_bytes" in payload["not_included"]


def test_profile_edit_explains_export_scope(client, app):
    owner_id = _seed_export(app); _login(client, owner_id)
    response = client.get("/profile/edit")
    assert b"Download your Ripple data" in response.data
    assert b"Download JSON export" in response.data
    assert b"visible direct messages" in response.data
    assert b"messages you deleted from your view" in response.data
    assert b"does not currently process creator-support payments" in response.data
    assert b"media references" in response.data
    assert b"does not package the media files themselves" in response.data



def test_export_removal_origin_distinguishes_owner_moderation_unknown_and_visible(client, app):
    with app.app_context():
        owner = User(username="origin_owner", email="origin-owner@example.com", password="owner-secret")
        moderator = User(username="origin_mod", email="origin-mod@example.com", password="mod-secret", is_admin=True)
        db.session.add_all([owner, moderator])
        db.session.flush()
        rows = [
            Tweet(content="visible", user_id=owner.id),
            Tweet(content="owner removed", user_id=owner.id, is_removed=True, removed_by_id=owner.id, removal_reason="Removed by author."),
            Tweet(content="moderated", user_id=owner.id, is_removed=True, removed_by_id=moderator.id, removal_reason="policy"),
            Tweet(content="legacy removed", user_id=owner.id, is_removed=True, removed_by_id=None, removal_reason="legacy"),
        ]
        db.session.add_all(rows)
        db.session.commit()
        owner_id = owner.id

    _login(client, owner_id)
    payload = client.get("/profile/export.json").get_json()
    by_content = {item["content"]: item for item in payload["posts"]}

    assert by_content["visible"]["removal_origin"] is None
    assert by_content["owner removed"]["removal_origin"] == "owner"
    assert by_content["moderated"]["removal_origin"] == "moderation"
    assert by_content["legacy removed"]["removal_origin"] == "unknown"

    exported = str(payload)
    assert "removed_by_id" not in exported
    assert "origin_mod" not in exported
