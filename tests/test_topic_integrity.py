"""Sprint 10 Story 10.5 integrity and correction coverage."""

from twitclone.contribution_models import ConstructiveContribution
from twitclone.extensions import db
from twitclone.models import Tweet, User
from twitclone.topic_evidence import topic_contribution_evidence
from twitclone.topic_models import Topic, TweetTopic, associate_topics
from twitclone.topic_reputation import topic_reputation_summaries


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


def _topic_post(app, user_id, *, content="Topic post #AWS", topics="AWS"):
    with app.app_context():
        tweet = Tweet(content=content, user_id=user_id)
        db.session.add(tweet)
        db.session.flush()
        associate_topics(tweet, explicit_raw=topics, content=content)
        db.session.commit()
        return tweet.id


def test_author_topic_correction_moves_derived_evidence(client, app):
    author_id = _user(app, "author")
    reviewer_id = _user(app, "reviewer")
    tweet_id = _topic_post(app, author_id, content="Containers on #AWS", topics="AWS")

    with app.app_context():
        db.session.add(
            ConstructiveContribution(user_id=reviewer_id, tweet_id=tweet_id, signal="helpful")
        )
        db.session.commit()
        assert topic_contribution_evidence(author_id, "aws")["total_constructive_signals"] == 1

    _login(client, author_id)
    response = client.post(
        f"/post/{tweet_id}/topics",
        data={"topics": "DevOps"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Post topics updated" in response.data

    with app.app_context():
        aws = topic_contribution_evidence(author_id, "aws")
        devops = topic_contribution_evidence(author_id, "devops")
        assert aws["total_constructive_signals"] == 0
        assert devops["total_constructive_signals"] == 1
        rows = TweetTopic.query.filter_by(tweet_id=tweet_id).all()
        sources = {row.topic.slug: row.source for row in rows}
        assert sources == {"aws": "hashtag", "devops": "explicit"}


def test_non_author_cannot_correct_topics(client, app):
    author_id = _user(app, "topic_owner")
    other_id = _user(app, "topic_other")
    tweet_id = _topic_post(app, author_id)
    _login(client, other_id)

    response = client.post(f"/post/{tweet_id}/topics", data={"topics": "DevOps"})
    assert response.status_code == 403

    with app.app_context():
        rows = TweetTopic.query.filter_by(tweet_id=tweet_id).all()
        assert {(row.topic.slug, row.source) for row in rows} == {("aws", "explicit")}


def test_clearing_explicit_topics_preserves_hashtag_discovery_only(client, app):
    author_id = _user(app, "clear_author")
    reviewer_id = _user(app, "clear_reviewer")
    tweet_id = _topic_post(app, author_id, content="Working in #AWS", topics="AWS")
    with app.app_context():
        db.session.add(
            ConstructiveContribution(user_id=reviewer_id, tweet_id=tweet_id, signal="thoughtful")
        )
        db.session.commit()

    _login(client, author_id)
    client.post(f"/post/{tweet_id}/topics", data={"topics": ""})

    with app.app_context():
        row = TweetTopic.query.filter_by(tweet_id=tweet_id).one()
        assert row.topic.slug == "aws"
        assert row.source == "hashtag"
        assert topic_contribution_evidence(author_id, "aws")["total_constructive_signals"] == 0
        assert topic_reputation_summaries(author_id) == []


def test_toggled_signal_immediately_stops_contributing(client, app):
    author_id = _user(app, "toggle_author")
    reviewer_id = _user(app, "toggle_reviewer")
    tweet_id = _topic_post(app, author_id, content="AWS post", topics="AWS")
    _login(client, reviewer_id)

    client.post(f"/post/{tweet_id}/contribution/helpful")
    with app.app_context():
        assert topic_contribution_evidence(author_id, "aws")["total_constructive_signals"] == 1

    client.post(f"/post/{tweet_id}/contribution/helpful")
    with app.app_context():
        assert topic_contribution_evidence(author_id, "aws")["total_constructive_signals"] == 0


def test_one_person_using_multiple_signal_types_is_one_unique_recognizer(app):
    author_id = _user(app, "multi_author")
    reviewer_id = _user(app, "multi_reviewer")
    tweet_id = _topic_post(app, author_id, content="Explicit AWS", topics="AWS")
    with app.app_context():
        db.session.add_all(
            [
                ConstructiveContribution(user_id=reviewer_id, tweet_id=tweet_id, signal="helpful"),
                ConstructiveContribution(user_id=reviewer_id, tweet_id=tweet_id, signal="thoughtful"),
                ConstructiveContribution(user_id=reviewer_id, tweet_id=tweet_id, signal="context"),
            ]
        )
        db.session.commit()
        evidence = topic_contribution_evidence(author_id, "aws")
        assert evidence["total_constructive_signals"] == 3
        assert evidence["unique_recognizers"] == 1


def test_removed_source_content_drops_from_summary_and_discovery(app):
    author_id = _user(app, "removed_author")
    reviewer_id = _user(app, "removed_reviewer")
    tweet_id = _topic_post(app, author_id, content="AWS material", topics="AWS")
    with app.app_context():
        db.session.add(
            ConstructiveContribution(user_id=reviewer_id, tweet_id=tweet_id, signal="context")
        )
        db.session.commit()
        assert topic_reputation_summaries(author_id)
        tweet = db.session.get(Tweet, tweet_id)
        tweet.is_removed = True
        db.session.commit()
        assert topic_reputation_summaries(author_id) == []
        assert topic_contribution_evidence(author_id, "aws")["eligible_posts"] == 0


def test_topic_correction_control_is_visible_only_to_author(client, app):
    author_id = _user(app, "ui_author")
    viewer_id = _user(app, "ui_viewer")
    tweet_id = _topic_post(app, author_id, content="AWS details", topics="AWS")

    _login(client, author_id)
    author_response = client.get(f"/post/{tweet_id}")
    assert b"Correct post topics" in author_response.data
    assert b"Reputation integrity" in author_response.data

    _login(client, viewer_id)
    viewer_response = client.get(f"/post/{tweet_id}")
    assert b"Correct post topics" not in viewer_response.data
