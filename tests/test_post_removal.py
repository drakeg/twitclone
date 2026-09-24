"""Sprint 21 author-requested original post removal coverage."""

from datetime import datetime

from twitclone.extensions import db
from twitclone.fact_context_models import FactContextSubmission
from twitclone.models import Bookmark, Notification, PostReport, Quote, Retweet, Tweet, User
from twitclone.reply_models import Reply


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _users_and_post(app, *, scheduled_at=None):
    with app.app_context():
        author = User(username="author", email="author@example.com", password="hash")
        other = User(username="other", email="other@example.com", password="hash")
        db.session.add_all([author, other])
        db.session.flush()
        tweet = Tweet(
            content="original post",
            user_id=author.id,
            scheduled_at=scheduled_at,
        )
        db.session.add(tweet)
        db.session.commit()
        return author.id, other.id, tweet.id


def test_anonymous_user_cannot_remove_post(client, app):
    _, _, tweet_id = _users_and_post(app)

    response = client.post(f"/post/{tweet_id}/remove")

    assert response.status_code == 302
    assert response.headers["Location"].startswith("/login?")
    with app.app_context():
        assert db.session.get(Tweet, tweet_id).is_removed is False


def test_non_owner_cannot_remove_post(client, app):
    _, other_id, tweet_id = _users_and_post(app)
    _login(client, other_id)

    response = client.post(f"/post/{tweet_id}/remove")

    assert response.status_code == 403
    with app.app_context():
        assert db.session.get(Tweet, tweet_id).is_removed is False


def test_owner_removal_soft_hides_post_and_records_author_semantics(client, app):
    author_id, _, tweet_id = _users_and_post(app)
    _login(client, author_id)

    response = client.post(f"/post/{tweet_id}/remove")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    with app.app_context():
        tweet = db.session.get(Tweet, tweet_id)
        assert tweet.is_removed is True
        assert tweet.removed_at is not None
        assert tweet.removed_by_id == author_id
        assert tweet.removal_reason == "Removed by author."


def test_author_removal_preserves_related_history_and_pending_report(client, app):
    author_id, other_id, tweet_id = _users_and_post(app)
    with app.app_context():
        quote = Quote(content="quoted response", user_id=other_id, tweet_id=tweet_id)
        retweet = Retweet(user_id=other_id, tweet_id=tweet_id)
        bookmark = Bookmark(user_id=other_id, tweet_id=tweet_id)
        notification = Notification(
            user_id=other_id,
            message="Historical notification",
            tweet_id=tweet_id,
        )
        report = PostReport(
            reporter_id=other_id,
            author_id=author_id,
            content_type="tweet",
            content_id=tweet_id,
            category="other",
            status="pending",
        )
        context = FactContextSubmission(
            tweet_id=tweet_id,
            submitter_id=other_id,
            claim="Claim under review",
            context="Context remains historically attached.",
            source_url="https://example.com/source",
        )
        reply = Reply(
            tweet_id=tweet_id,
            user_id=other_id,
            content="existing reply",
        )
        db.session.add_all(
            [quote, retweet, bookmark, notification, report, context, reply]
        )
        db.session.commit()
    _login(client, author_id)

    client.post(f"/post/{tweet_id}/remove")

    with app.app_context():
        assert Tweet.query.count() == 1
        assert Quote.query.filter_by(tweet_id=tweet_id).count() == 1
        assert Retweet.query.filter_by(tweet_id=tweet_id).count() == 1
        assert Bookmark.query.filter_by(tweet_id=tweet_id).count() == 1
        assert Notification.query.filter_by(tweet_id=tweet_id).count() == 1
        assert FactContextSubmission.query.filter_by(tweet_id=tweet_id).count() == 1
        assert Reply.query.filter_by(tweet_id=tweet_id).count() == 1
        persisted_report = PostReport.query.filter_by(
            content_type="tweet",
            content_id=tweet_id,
        ).one()
        assert persisted_report.status == "pending"


def test_removed_post_disappears_from_public_surfaces(client, app):
    author_id, other_id, tweet_id = _users_and_post(app)
    with app.app_context():
        db.session.add(Bookmark(user_id=other_id, tweet_id=tweet_id))
        db.session.commit()
    _login(client, author_id)
    client.post(f"/post/{tweet_id}/remove")

    assert client.get(f"/post/{tweet_id}").status_code == 404
    assert client.get(f"/post/{tweet_id}/thread").status_code == 404

    home = client.get("/")
    assert b"original post" not in home.data

    _login(client, other_id)
    bookmarks = client.get("/bookmarks")
    assert bookmarks.status_code == 200
    assert b"original post" not in bookmarks.data


def test_future_scheduled_post_is_not_removed_through_published_post_flow(client, app):
    author_id, _, tweet_id = _users_and_post(
        app,
        scheduled_at=datetime(2099, 1, 1, 12, 0),
    )
    _login(client, author_id)

    response = client.post(f"/post/{tweet_id}/remove")

    assert response.status_code == 404
    with app.app_context():
        tweet = db.session.get(Tweet, tweet_id)
        assert tweet.is_removed is False
        assert tweet.removed_at is None


def test_owner_detail_exposes_removal_control_only_to_owner(client, app):
    author_id, other_id, tweet_id = _users_and_post(app)

    _login(client, author_id)
    owner_view = client.get(f"/post/{tweet_id}")
    assert owner_view.status_code == 200
    assert b"Remove post" in owner_view.data
    assert b"retains related historical records" in owner_view.data

    _login(client, other_id)
    other_view = client.get(f"/post/{tweet_id}")
    assert other_view.status_code == 200
    assert b"Remove post" not in other_view.data
