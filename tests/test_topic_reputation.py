"""Sprint 10 Story 10.3 topic reputation summary coverage."""

from twitclone.contribution_models import ConstructiveContribution
from twitclone.extensions import db
from twitclone.models import Entitlement, Tweet, User
from twitclone.topic_models import Topic, TweetTopic
from twitclone.topic_reputation import topic_reputation_level, topic_reputation_summaries, topic_reputation_summary


def _user(app, username):
    with app.app_context():
        user = User(username=username, email=f"{username}@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _topic_post(app, author_id, topic_name="AWS"):
    with app.app_context():
        topic = Topic.query.filter_by(slug=topic_name.lower()).first()
        if topic is None:
            topic = Topic(name=topic_name, slug=topic_name.lower())
            db.session.add(topic)
            db.session.flush()
        tweet = Tweet(content=f"A useful {topic_name} post", user_id=author_id)
        db.session.add(tweet)
        db.session.flush()
        db.session.add(TweetTopic(tweet_id=tweet.id, topic_id=topic.id, source="explicit"))
        db.session.commit()
        return tweet.id, topic.slug


def _recognize(app, recognizer_id, tweet_id, signal):
    with app.app_context():
        db.session.add(
            ConstructiveContribution(user_id=recognizer_id, tweet_id=tweet_id, signal=signal)
        )
        db.session.commit()


def test_reputation_levels_use_transparent_multi_dimension_thresholds():
    base = {
        "eligible_posts": 3,
        "recognized_posts": 0,
        "unique_recognizers": 0,
        "total_constructive_signals": 0,
    }
    assert topic_reputation_level(base) == "Building contribution history"

    emerging = {**base, "recognized_posts": 1, "unique_recognizers": 1, "total_constructive_signals": 1}
    assert topic_reputation_level(emerging) == "Emerging contributor"

    recognized = {**base, "recognized_posts": 2, "unique_recognizers": 2, "total_constructive_signals": 3}
    assert topic_reputation_level(recognized) == "Recognized contributor"

    established = {**base, "recognized_posts": 3, "unique_recognizers": 3, "total_constructive_signals": 5}
    assert topic_reputation_level(established) == "Established contributor"


def test_summary_exposes_underlying_evidence(app):
    author_id = _user(app, "author")
    recognizer_id = _user(app, "reader")
    tweet_id, topic_slug = _topic_post(app, author_id)
    _recognize(app, recognizer_id, tweet_id, "helpful")

    with app.app_context():
        summary = topic_reputation_summary(author_id, topic_slug)
        assert summary["level"] == "Emerging contributor"
        assert summary["evidence"]["eligible_posts"] == 1
        assert summary["evidence"]["recognized_posts"] == 1
        assert summary["evidence"]["unique_recognizers"] == 1
        assert summary["evidence"]["signals"]["helpful"]["count"] == 1
        assert "Followers" in summary["explanation"]
        assert "paid plans" in summary["explanation"]


def test_hashtag_only_topics_do_not_get_reputation_summary(app):
    author_id = _user(app, "hashtag_author")
    with app.app_context():
        topic = Topic(name="Python", slug="python")
        tweet = Tweet(content="Learning #Python", user_id=author_id)
        db.session.add_all([topic, tweet])
        db.session.flush()
        db.session.add(TweetTopic(tweet_id=tweet.id, topic_id=topic.id, source="hashtag"))
        db.session.commit()

        assert topic_reputation_summaries(author_id) == []


def test_paid_entitlement_does_not_change_topic_summary(app):
    author_id = _user(app, "paid_author")
    recognizer_id = _user(app, "paid_reader")
    tweet_id, topic_slug = _topic_post(app, author_id)
    _recognize(app, recognizer_id, tweet_id, "thoughtful")

    with app.app_context():
        before = topic_reputation_summary(author_id, topic_slug)
        db.session.add(Entitlement(user_id=author_id, key="ripple_plus", active=True, source="test"))
        db.session.commit()
        after = topic_reputation_summary(author_id, topic_slug)
        assert after["level"] == before["level"]
        assert after["evidence"]["total_constructive_signals"] == before["evidence"]["total_constructive_signals"]


def test_profile_renders_explainable_topic_summary(client, app):
    author_id = _user(app, "profile_author")
    viewer_id = _user(app, "profile_viewer")
    tweet_id, _ = _topic_post(app, author_id)
    _recognize(app, viewer_id, tweet_id, "context")
    _login(client, viewer_id)

    response = client.get("/profile/profile_author")

    assert response.status_code == 200
    assert b"Topic reputation" in response.data
    assert b"AWS" in response.data
    assert b"Emerging contributor" in response.data
    assert b"1 unique recognizer" in response.data
    assert b"Useful context" in response.data
    assert b"do not affect feed ranking or moderation authority" in response.data
