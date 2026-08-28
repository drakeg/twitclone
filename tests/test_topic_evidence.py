"""Sprint 10 Story 10.2 topic-contribution evidence coverage."""

from twitclone.contribution_models import ConstructiveContribution
from twitclone.extensions import db
from twitclone.models import Tweet, User
from twitclone.topic_evidence import topic_contribution_evidence
from twitclone.topic_models import Topic, TweetTopic


def _user(app, username):
    with app.app_context():
        user = User(username=username, email=f"{username}@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        return user.id


def _topic(app, name="AWS", slug="aws"):
    with app.app_context():
        topic = Topic(name=name, slug=slug)
        db.session.add(topic)
        db.session.commit()
        return topic.id


def _tweet_with_topic(app, *, author_id, topic_id, source="explicit", removed=False):
    with app.app_context():
        tweet = Tweet(content="Topic contribution", user_id=author_id, is_removed=removed)
        db.session.add(tweet)
        db.session.flush()
        db.session.add(TweetTopic(tweet_id=tweet.id, topic_id=topic_id, source=source))
        db.session.commit()
        return tweet.id


def test_explicit_topic_constructive_signals_are_derived_as_evidence(app):
    author_id = _user(app, "author")
    reviewer_one = _user(app, "reviewer1")
    reviewer_two = _user(app, "reviewer2")
    topic_id = _topic(app)
    tweet_id = _tweet_with_topic(app, author_id=author_id, topic_id=topic_id)

    with app.app_context():
        db.session.add_all(
            [
                ConstructiveContribution(user_id=reviewer_one, tweet_id=tweet_id, signal="helpful"),
                ConstructiveContribution(user_id=reviewer_one, tweet_id=tweet_id, signal="context"),
                ConstructiveContribution(user_id=reviewer_two, tweet_id=tweet_id, signal="thoughtful"),
            ]
        )
        db.session.commit()

        evidence = topic_contribution_evidence(author_id, "aws")

        assert evidence["eligible_posts"] == 1
        assert evidence["recognized_posts"] == 1
        assert evidence["unique_recognizers"] == 2
        assert evidence["signals"]["helpful"]["count"] == 1
        assert evidence["signals"]["thoughtful"]["count"] == 1
        assert evidence["signals"]["context"]["count"] == 1
        assert evidence["total_constructive_signals"] == 3


def test_hashtag_only_topic_does_not_count_as_expertise_evidence(app):
    author_id = _user(app, "author")
    reviewer_id = _user(app, "reviewer")
    topic_id = _topic(app)
    tweet_id = _tweet_with_topic(app, author_id=author_id, topic_id=topic_id, source="hashtag")

    with app.app_context():
        db.session.add(
            ConstructiveContribution(user_id=reviewer_id, tweet_id=tweet_id, signal="helpful")
        )
        db.session.commit()

        evidence = topic_contribution_evidence(author_id, "aws")

        assert evidence["eligible_posts"] == 0
        assert evidence["total_constructive_signals"] == 0


def test_removed_posts_and_self_signals_do_not_count(app):
    author_id = _user(app, "author")
    reviewer_id = _user(app, "reviewer")
    topic_id = _topic(app)
    visible_tweet_id = _tweet_with_topic(app, author_id=author_id, topic_id=topic_id)
    removed_tweet_id = _tweet_with_topic(
        app, author_id=author_id, topic_id=topic_id, removed=True
    )

    with app.app_context():
        db.session.add_all(
            [
                ConstructiveContribution(user_id=author_id, tweet_id=visible_tweet_id, signal="helpful"),
                ConstructiveContribution(user_id=reviewer_id, tweet_id=removed_tweet_id, signal="context"),
            ]
        )
        db.session.commit()

        evidence = topic_contribution_evidence(author_id, "aws")

        assert evidence["eligible_posts"] == 1
        assert evidence["total_constructive_signals"] == 0
        assert evidence["unique_recognizers"] == 0


def test_evidence_is_recomputed_when_signal_is_removed(app):
    author_id = _user(app, "author")
    reviewer_id = _user(app, "reviewer")
    topic_id = _topic(app)
    tweet_id = _tweet_with_topic(app, author_id=author_id, topic_id=topic_id)

    with app.app_context():
        row = ConstructiveContribution(user_id=reviewer_id, tweet_id=tweet_id, signal="helpful")
        db.session.add(row)
        db.session.commit()
        assert topic_contribution_evidence(author_id, "aws")["total_constructive_signals"] == 1

        db.session.delete(row)
        db.session.commit()
        assert topic_contribution_evidence(author_id, "aws")["total_constructive_signals"] == 0


def test_unknown_topic_returns_none(app):
    author_id = _user(app, "author")
    with app.app_context():
        assert topic_contribution_evidence(author_id, "does-not-exist") is None


def test_rules_explicitly_exclude_popularity_and_paid_status(app):
    author_id = _user(app, "author")
    _topic(app)

    with app.app_context():
        evidence = topic_contribution_evidence(author_id, "aws")
        assert evidence["rules"] == {
            "explicit_topics_only": True,
            "removed_posts_excluded": True,
            "self_signals_excluded": True,
            "followers_excluded": True,
            "impressions_excluded": True,
            "paid_status_excluded": True,
        }
