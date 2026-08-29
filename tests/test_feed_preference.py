"""Sprint 12 Story 12.2 persistent feed preference coverage."""

from twitclone.extensions import db
from twitclone.feed_preferences import UserFeedPreference
from twitclone.models import Follows, Tweet, User


def _users(app):
    with app.app_context():
        viewer = User(username="pref_viewer", email="pref-viewer@example.com", password="hash")
        followed = User(username="pref_followed", email="pref-followed@example.com", password="hash")
        stranger = User(username="pref_stranger", email="pref-stranger@example.com", password="hash")
        db.session.add_all([viewer, followed, stranger]); db.session.flush()
        db.session.add(Follows(follower_id=viewer.id, followed_id=followed.id))
        db.session.add_all([
            Tweet(content="followed default content", user_id=followed.id),
            Tweet(content="stranger default content", user_id=stranger.id),
        ])
        db.session.commit()
        return viewer.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_saved_following_preference_becomes_default_home_feed(client, app):
    viewer_id = _users(app)
    with app.app_context():
        db.session.add(UserFeedPreference(user_id=viewer_id, feed_mode="following")); db.session.commit()
    _login(client, viewer_id)

    response = client.get("/")
    assert response.status_code == 200
    assert b"followed default content" in response.data
    assert b"stranger default content" not in response.data
    assert b"Your default is <strong>Following</strong>" in response.data
    assert b"Current default" in response.data


def test_temporary_switch_does_not_change_stored_default(client, app):
    viewer_id = _users(app)
    with app.app_context():
        db.session.add(UserFeedPreference(user_id=viewer_id, feed_mode="following")); db.session.commit()
    _login(client, viewer_id)

    response = client.get("/?feed=all")
    assert b"stranger default content" in response.data
    assert b"Make All Ripple my default" in response.data
    with app.app_context():
        assert db.session.get(UserFeedPreference, viewer_id).feed_mode == "following"


def test_user_can_replace_default_and_home_uses_new_value(client, app):
    viewer_id = _users(app)
    _login(client, viewer_id)

    response = client.post("/feed-preference", data={"feed_mode": "following"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Following is now your default feed" in response.data
    with app.app_context():
        assert db.session.get(UserFeedPreference, viewer_id).feed_mode == "following"

    response = client.get("/")
    assert b"followed default content" in response.data
    assert b"stranger default content" not in response.data

    client.post("/feed-preference", data={"feed_mode": "all"})
    with app.app_context():
        assert db.session.get(UserFeedPreference, viewer_id).feed_mode == "all"


def test_invalid_preference_is_rejected_without_mutation(client, app):
    viewer_id = _users(app)
    _login(client, viewer_id)

    response = client.post("/feed-preference", data={"feed_mode": "engagement"})
    assert response.status_code == 400
    with app.app_context():
        assert db.session.get(UserFeedPreference, viewer_id) is None


def test_feed_preference_requires_authentication(client):
    response = client.post("/feed-preference", data={"feed_mode": "following"})
    assert response.status_code in {302, 401}
