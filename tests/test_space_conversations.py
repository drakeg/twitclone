"""Sprint 13 Story 13.2 space-scoped conversation coverage."""

from datetime import UTC, datetime

from twitclone.extensions import db
from twitclone.models import Quote, Retweet, Tweet, User
from twitclone.spaces.models import Space, SpaceMembership, SpacePost
from twitclone.timeline.service import build_timeline_posts


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _space_fixture(app):
    with app.app_context():
        owner = User(username="space_chat_owner", email="space-chat-owner@example.com", password="hash")
        member = User(username="space_chat_member", email="space-chat-member@example.com", password="hash")
        outsider = User(username="space_chat_outsider", email="space-chat-outsider@example.com", password="hash")
        db.session.add_all([owner, member, outsider]); db.session.flush()
        space = Space(slug="rv-chat", name="RV Chat", description="Space conversations.", owner_id=owner.id)
        db.session.add(space); db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=space.id, user_id=owner.id, role="owner"),
            SpaceMembership(space_id=space.id, user_id=member.id, role="member"),
        ])
        db.session.commit()
        return space.id, owner.id, member.id, outsider.id


def test_member_can_publish_space_post_and_public_can_read_it(client, app):
    _, _, member_id, _ = _space_fixture(app)
    _login(client, member_id)
    response = client.post("/spaces/rv-chat/posts", data={"content": "Campground power setup"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Campground power setup" in response.data
    assert b"not part of the global timeline" in response.data
    with app.app_context():
        scoped = SpacePost.query.one()
        assert scoped.tweet.user_id == member_id
    public_response = client.get("/spaces/rv-chat")
    assert public_response.status_code == 200
    assert b"Campground power setup" in public_response.data


def test_nonmember_cannot_publish_space_post(client, app):
    _, _, _, outsider_id = _space_fixture(app)
    _login(client, outsider_id)
    response = client.post("/spaces/rv-chat/posts", data={"content": "Should not publish"})
    assert response.status_code == 403
    with app.app_context():
        assert SpacePost.query.count() == 0


def test_space_posts_do_not_appear_in_global_timeline_modes(app):
    space_id, _, member_id, _ = _space_fixture(app)
    with app.app_context():
        now = datetime.now(UTC).replace(tzinfo=None)
        global_post = Tweet(content="global post", user_id=member_id, timestamp=now)
        scoped_post = Tweet(content="space only", user_id=member_id, timestamp=now)
        db.session.add_all([global_post, scoped_post]); db.session.flush()
        db.session.add(SpacePost(space_id=space_id, tweet_id=scoped_post.id)); db.session.commit()
        viewer = db.session.get(User, member_id)
        for mode in ("all", "following", "quiet"):
            contents = {post["content"] for post in build_timeline_posts(now=now, viewer=viewer, feed_mode=mode)}
            assert "global post" in contents
            assert "space only" not in contents


def test_reposts_and_quotes_of_space_post_do_not_leak_to_global_feed(app):
    space_id, owner_id, member_id, outsider_id = _space_fixture(app)
    with app.app_context():
        now = datetime.now(UTC).replace(tzinfo=None)
        scoped_post = Tweet(content="scoped source", user_id=member_id, timestamp=now)
        db.session.add(scoped_post); db.session.flush()
        db.session.add_all([
            SpacePost(space_id=space_id, tweet_id=scoped_post.id),
            Retweet(user_id=owner_id, tweet_id=scoped_post.id, timestamp=now),
            Quote(content="quote leak", user_id=outsider_id, tweet_id=scoped_post.id, timestamp=now),
        ]); db.session.commit()
        posts = build_timeline_posts(now=now, feed_mode="all")
        assert not any(post["content"] in {"scoped source", "quote leak"} for post in posts)


def test_space_conversations_render_newest_first(client, app):
    space_id, _, member_id, _ = _space_fixture(app)
    with app.app_context():
        older = Tweet(content="older conversation", user_id=member_id, timestamp=datetime(2026, 8, 28, 10, 0, 0))
        newer = Tweet(content="newer conversation", user_id=member_id, timestamp=datetime(2026, 8, 28, 11, 0, 0))
        db.session.add_all([older, newer]); db.session.flush()
        db.session.add_all([SpacePost(space_id=space_id, tweet_id=older.id), SpacePost(space_id=space_id, tweet_id=newer.id)]); db.session.commit()
    response = client.get("/spaces/rv-chat")
    assert response.status_code == 200
    assert response.data.index(b"newer conversation") < response.data.index(b"older conversation")
