"""Sprint 12 Story 12.5 feed-integrity regression coverage."""

from datetime import UTC, datetime, timedelta

from twitclone.extensions import db
from twitclone.models import Follows, Tweet, User
from twitclone.timeline.integrity import (
    ALLOWED_INCLUSION_INPUTS,
    FORBIDDEN_RANKING_INPUTS,
    MEASUREMENT_POLICY,
    ORDERING_RULE,
)
from twitclone.timeline.service import build_timeline_posts
from twitclone.topic_models import Topic, TweetTopic


def _make_users():
    viewer = User(username="integrity_viewer", email="integrity-viewer@example.com", password="hash")
    mutual = User(username="integrity_mutual", email="integrity-mutual@example.com", password="hash")
    stranger = User(username="integrity_stranger", email="integrity-stranger@example.com", password="hash")
    db.session.add_all([viewer, mutual, stranger]); db.session.flush()
    db.session.add_all([
        Follows(follower_id=viewer.id, followed_id=mutual.id),
        Follows(follower_id=mutual.id, followed_id=viewer.id),
    ])
    db.session.commit()
    return viewer, mutual, stranger


def test_feed_integrity_policy_forbids_commercial_and_engagement_ranking_inputs():
    assert ORDERING_RULE == "newest-first"
    assert "follower count" in FORBIDDEN_RANKING_INPUTS
    assert "verification status" in FORBIDDEN_RANKING_INPUTS
    assert "paid subscription or entitlement" in FORBIDDEN_RANKING_INPUTS
    assert "engagement velocity" in FORBIDDEN_RANKING_INPUTS
    assert "timestamp" in ALLOWED_INCLUSION_INPUTS


def test_measurement_policy_keeps_reporting_signals_out_of_feed_ordering():
    assert MEASUREMENT_POLICY["existing_post_impressions"].endswith("after feed selection")
    assert MEASUREMENT_POLICY["profile_visits"].endswith("not feed ordering")
    assert MEASUREMENT_POLICY["follower_snapshots"].endswith("not feed ordering")
    assert MEASUREMENT_POLICY["feed_choice_history"] == "not collected by Sprint 12"
    assert MEASUREMENT_POLICY["topic_query_history"] == "not collected by Sprint 12"


def test_all_following_quiet_and_topic_are_newest_first(app):
    with app.app_context():
        viewer, mutual, stranger = _make_users()
        now = datetime.now(UTC).replace(tzinfo=None)
        older = Tweet(content="older explicit topic", user_id=mutual.id, timestamp=now - timedelta(minutes=3))
        newer = Tweet(content="newer explicit topic", user_id=mutual.id, timestamp=now - timedelta(minutes=1))
        unrelated = Tweet(content="newest unrelated", user_id=stranger.id, timestamp=now)
        db.session.add_all([older, newer, unrelated]); db.session.flush()
        topic = Topic(name="Integrity", slug="integrity")
        db.session.add(topic); db.session.flush()
        db.session.add_all([
            TweetTopic(tweet_id=older.id, topic_id=topic.id, source="explicit"),
            TweetTopic(tweet_id=newer.id, topic_id=topic.id, source="explicit"),
        ])
        db.session.commit()
        viewer = db.session.get(User, viewer.id)

        all_posts = build_timeline_posts(now=now, viewer=viewer, feed_mode="all")
        following_posts = build_timeline_posts(now=now, viewer=viewer, feed_mode="following")
        quiet_posts = build_timeline_posts(now=now, viewer=viewer, feed_mode="quiet")
        topic_posts = build_timeline_posts(now=now, viewer=viewer, feed_mode="topic", topic_slug="integrity")

        for posts in (all_posts, following_posts, quiet_posts, topic_posts):
            timestamps = [post["timestamp"] for post in posts]
            assert timestamps == sorted(timestamps, reverse=True)

        assert [post["content"] for post in topic_posts] == ["newer explicit topic", "older explicit topic"]
