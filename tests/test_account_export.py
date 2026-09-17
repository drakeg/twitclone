"""Sprint 18 Story 18.1 user-controlled portability coverage."""

from twitclone.extensions import db
from twitclone.models import Follows, Quote, Tweet, User
from twitclone.reply_models import Reply
from twitclone.resource_models import Resource, ResourceRevision
from twitclone.spaces.models import Space, SpaceMembership


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _seed_export(app):
    with app.app_context():
        owner = User(username="export_owner", email="owner@example.com", password="secret-hash", bio="Portable profile")
        follower = User(username="export_follower", email="follower@example.com", password="other-secret")
        outsider = User(username="export_outsider", email="outsider@example.com", password="outside-secret")
        db.session.add_all([owner, follower, outsider]); db.session.flush()
        db.session.add_all([
            Follows(follower_id=owner.id, followed_id=follower.id),
            Follows(follower_id=follower.id, followed_id=owner.id),
        ])
        owner_post = Tweet(content="Owner portable post", user_id=owner.id)
        outsider_post = Tweet(content="Outsider private-to-export post", user_id=outsider.id)
        db.session.add_all([owner_post, outsider_post]); db.session.flush()
        db.session.add(Quote(content="Owner quote", user_id=owner.id, tweet_id=outsider_post.id))
        db.session.add(Reply(content="Owner reply", user_id=owner.id, tweet_id=outsider_post.id))
        removed = Tweet(content="Owner removed post", user_id=owner.id, is_removed=True, removal_reason="author record")
        db.session.add(removed)
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
    assert payload["version"] == 1
    assert payload["account"]["email"] == "owner@example.com"
    assert payload["social_graph"] == {"following": ["export_follower"], "followers": ["export_follower"]}
    assert [item["content"] for item in payload["posts"]] == ["Owner portable post", "Owner removed post"]
    assert payload["posts"][1]["is_removed"] is True
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


def test_profile_edit_explains_export_scope(client, app):
    owner_id = _seed_export(app); _login(client, owner_id)
    response = client.get("/profile/edit")
    assert b"Download your Ripple data" in response.data
    assert b"Download JSON export" in response.data
    assert b"does not include passwords, private messages" in response.data
