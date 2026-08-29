"""Sprint 12 Story 12.3 topic-oriented discovery coverage."""

from datetime import UTC, datetime, timedelta

from twitclone.extensions import db
from twitclone.models import Poll, Quote, Retweet, Tweet, User
from twitclone.timeline.service import build_timeline_posts
from twitclone.topic_models import Topic, TweetTopic


def _user(app, username):
    with app.app_context():
        user = User(username=username, email=f"{username}@example.com", password="hash")
        db.session.add(user); db.session.commit(); return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id); session["_fresh"] = True


def _topic_post(app, user_id, *, content, topic_name="AWS", source="explicit", timestamp=None):
    with app.app_context():
        topic = Topic.query.filter_by(slug="aws").first()
        if topic is None:
            topic = Topic(name=topic_name, slug="aws"); db.session.add(topic); db.session.flush()
        tweet = Tweet(content=content, user_id=user_id, timestamp=timestamp or datetime.now(UTC).replace(tzinfo=None))
        db.session.add(tweet); db.session.flush()
        db.session.add(TweetTopic(tweet_id=tweet.id, topic_id=topic.id, source=source)); db.session.commit()
        return tweet.id


def test_topic_feed_uses_explicit_associations_only(app):
    author_id = _user(app, "topic_author")
    explicit_id = _topic_post(app, author_id, content="explicit aws", source="explicit")
    _topic_post(app, author_id, content="hashtag aws", source="hashtag")
    with app.app_context():
        posts = build_timeline_posts(now=datetime.now(UTC).replace(tzinfo=None), feed_mode="topic", topic_slug="aws")
        assert [post["action_tweet_id"] for post in posts] == [explicit_id]
        assert posts[0]["content"] == "explicit aws"


def test_topic_feed_includes_reposts_of_explicit_topic_posts_but_not_quotes_or_polls(app):
    author_id = _user(app, "topic_source_author")
    reposter_id = _user(app, "topic_reposter")
    source_id = _topic_post(app, author_id, content="topic source", source="explicit", timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1))
    with app.app_context():
        now = datetime.now(UTC).replace(tzinfo=None)
        db.session.add_all([
            Retweet(user_id=reposter_id, tweet_id=source_id, timestamp=now - timedelta(minutes=2)),
            Quote(user_id=reposter_id, tweet_id=source_id, content="quote about topic", timestamp=now - timedelta(minutes=1)),
            Poll(question="topic poll", user_id=reposter_id, created_at=now, duration_days=1, duration_hours=0, duration_minutes=0),
        ]); db.session.commit()
        posts = build_timeline_posts(now=now, feed_mode="topic", topic_slug="aws")
        assert any(post["type"] == "tweet" and post["action_tweet_id"] == source_id for post in posts)
        assert any(post["type"] == "retweet" and post["action_tweet_id"] == source_id for post in posts)
        assert not any(post["type"] == "quote" for post in posts)
        assert not any(post["type"] == "poll" for post in posts)


def test_topic_feed_ui_explains_rules_and_preserves_topic_pagination(client, app):
    viewer_id = _user(app, "topic_viewer")
    author_id = _user(app, "topic_page_author")
    now = datetime.now(UTC).replace(tzinfo=None)
    for number in range(22):
        _topic_post(app, author_id, content=f"aws post {number}", source="explicit", timestamp=now - timedelta(seconds=number))
    _login(client, viewer_id)

    response = client.get("/?feed=topic&topic=AWS")
    assert response.status_code == 200
    assert b"explicitly tagged by their authors" in response.data
    assert b"Hashtag-only matches" in response.data
    assert b"topic=aws" in response.data
    assert b"page=2" in response.data


def test_topic_feed_unknown_topic_has_clear_empty_state(client, app):
    viewer_id = _user(app, "topic_empty_viewer")
    _login(client, viewer_id)
    response = client.get("/?feed=topic&topic=NoSuchTopic")
    assert response.status_code == 200
    assert b"No explicit posts for this topic yet" in response.data
    assert b"NoSuchTopic" in response.data


def test_topic_mode_cannot_be_saved_as_default(client, app):
    viewer_id = _user(app, "topic_pref_viewer")
    _login(client, viewer_id)
    response = client.post("/feed-preference", data={"feed_mode": "topic"})
    assert response.status_code == 400
