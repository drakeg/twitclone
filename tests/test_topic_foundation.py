"""Sprint 10 Story 10.1 topic-foundation regression coverage."""

from twitclone.extensions import db
from twitclone.models import Tweet, User
from twitclone.topic_models import (
    Topic,
    TweetTopic,
    explicit_topic_values,
    hashtag_topic_values,
    normalize_topic_name,
    public_topic_associations,
    topic_slug,
)


def _user(app, username="topic_author"):
    with app.app_context():
        user = User(username=username, email=f"{username}@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_topic_normalization_and_duplicate_safe_values():
    assert normalize_topic_name("  #RV   Travel  ") == "RV Travel"
    assert topic_slug("RV Travel") == "rv-travel"
    assert explicit_topic_values("RV Travel, rv travel, AWS, , AWS") == [
        ("RV Travel", "rv-travel"),
        ("AWS", "aws"),
    ]


def test_hashtags_create_deterministic_candidates_without_sensitive_inference():
    assert hashtag_topic_values("Talking about #RV_Travel and #AWS today. #AWS") == [
        ("RV Travel", "rv-travel"),
        ("AWS", "aws"),
    ]
    assert hashtag_topic_values("No hashtags here") == []


def test_anonymous_user_cannot_create_post_topics(client, app):
    response = client.post(
        "/tweet",
        data={"content": "Unauthorized topic post", "topics": "AWS"},
    )

    assert response.status_code in (302, 401)
    with app.app_context():
        assert Tweet.query.count() == 0
        assert Topic.query.count() == 0
        assert TweetTopic.query.count() == 0


def test_post_creation_records_explicit_and_hashtag_sources(client, app):
    user_id = _user(app)
    _login(client, user_id)

    response = client.post(
        "/tweet",
        data={
            "content": "Working on containers for #AWS",
            "conversation_intent": "open",
            "topics": "DevOps, AWS",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    with app.app_context():
        tweet = Tweet.query.filter_by(user_id=user_id).one()
        associations = {
            row.topic.slug: row.source for row in TweetTopic.query.filter_by(tweet_id=tweet.id).all()
        }
        assert associations == {"devops": "explicit", "aws": "explicit"}
        assert Topic.query.filter_by(slug="aws").count() == 1


def test_hashtag_only_post_records_hashtag_source(client, app):
    user_id = _user(app)
    _login(client, user_id)

    client.post(
        "/tweet",
        data={"content": "Learning more about #Python", "conversation_intent": "open"},
    )

    with app.app_context():
        tweet = Tweet.query.filter_by(user_id=user_id).one()
        association = TweetTopic.query.filter_by(tweet_id=tweet.id).one()
        assert association.topic.slug == "python"
        assert association.source == "hashtag"


def test_legacy_posts_require_no_topic_backfill_and_removed_posts_are_not_public(app):
    user_id = _user(app)
    with app.app_context():
        legacy = Tweet(content="Legacy post without topics", user_id=user_id)
        removed = Tweet(content="Removed #AWS post", user_id=user_id, is_removed=True)
        db.session.add_all([legacy, removed])
        db.session.commit()

        assert legacy.topic_associations == []
        assert public_topic_associations(legacy) == []
        assert public_topic_associations(removed) == []


def test_timeline_shows_explicit_topics(client, app):
    user_id = _user(app)
    _login(client, user_id)
    client.post(
        "/tweet",
        data={
            "content": "A practical towing discussion",
            "conversation_intent": "open",
            "topics": "RV Towing",
        },
    )

    response = client.get("/")

    assert response.status_code == 200
    assert b"Post topics" in response.data
    assert b"RV Towing" in response.data
