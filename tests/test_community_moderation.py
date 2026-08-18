"""Regression coverage for Ripple Community Standards and moderation."""

from twitclone.community.routes import COMMUNITY_GUIDELINES_VERSION
from twitclone.extensions import db
from twitclone.models import Notification, PostReport, Tweet, User


def _user(app, username, *, admin=False, accepted=True):
    with app.app_context():
        user = User(
            username=username,
            email=f"{username}@example.com",
            password="hash",
            is_admin=admin,
            community_guidelines_version=COMMUNITY_GUIDELINES_VERSION if accepted else None,
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_guidelines_are_public_and_clear(client):
    response = client.get("/community-guidelines")
    assert response.status_code == 200
    assert b"Ripple Community Standards" in response.data
    assert b"No bullying or harassment" in response.data
    assert b"Disagree with ideas, not dignity" in response.data


def test_existing_user_must_accept_current_guidelines(client, app):
    user_id = _user(app, "legacy", accepted=False)
    _login(client, user_id)
    previous = app.config.get("ENFORCE_COMMUNITY_GUIDELINES_IN_TESTS", False)
    app.config["ENFORCE_COMMUNITY_GUIDELINES_IN_TESTS"] = True
    try:
        response = client.get("/")
        assert response.status_code == 302
        assert "/community-guidelines/accept" in response.headers["Location"]

        accepted = client.post("/community-guidelines/accept", data={"accept": "yes"})
        assert accepted.status_code == 302
        with app.app_context():
            user = db.session.get(User, user_id)
            assert user.community_guidelines_version == COMMUNITY_GUIDELINES_VERSION
            assert user.community_guidelines_accepted_at is not None
    finally:
        app.config["ENFORCE_COMMUNITY_GUIDELINES_IN_TESTS"] = previous


def test_user_can_report_another_users_post_once(client, app):
    author_id = _user(app, "author")
    reporter_id = _user(app, "reporter")
    with app.app_context():
        tweet = Tweet(content="Hostile post", user_id=author_id)
        db.session.add(tweet)
        db.session.commit()
        tweet_id = tweet.id

    _login(client, reporter_id)
    response = client.post(
        f"/report/tweet/{tweet_id}",
        data={"category": "bullying", "details": "Repeated personal attack."},
    )
    assert response.status_code == 302
    with app.app_context():
        report = PostReport.query.one()
        assert report.author_id == author_id
        assert report.reporter_id == reporter_id
        assert report.category == "bullying"
        assert report.status == "pending"

    duplicate = client.post(f"/report/tweet/{tweet_id}", data={"category": "bullying"})
    assert duplicate.status_code == 302
    with app.app_context():
        assert PostReport.query.count() == 1


def test_pending_report_is_obvious_to_admin_and_removal_hides_content(client, app):
    author_id = _user(app, "author")
    reporter_id = _user(app, "reporter")
    admin_id = _user(app, "moderator", admin=True)
    with app.app_context():
        tweet = Tweet(content="Content under review", user_id=author_id)
        db.session.add(tweet)
        db.session.flush()
        report = PostReport(
            reporter_id=reporter_id,
            author_id=author_id,
            content_type="tweet",
            content_id=tweet.id,
            category="abuse",
        )
        db.session.add(report)
        db.session.commit()
        tweet_id, report_id = tweet.id, report.id

    _login(client, admin_id)
    dashboard = client.get("/admin")
    assert dashboard.status_code == 200
    assert b"Reports awaiting review" in dashboard.data
    assert b"Moderation" in dashboard.data

    result = client.post(
        f"/admin/moderation/{report_id}",
        data={"action": "remove", "resolution_notes": "Personal attack."},
    )
    assert result.status_code == 302
    with app.app_context():
        tweet = db.session.get(Tweet, tweet_id)
        report = db.session.get(PostReport, report_id)
        assert tweet.is_removed is True
        assert report.status == "removed"
        assert Notification.query.filter_by(user_id=author_id).count() == 1

    timeline = client.get("/")
    assert b"Content under review" not in timeline.data
    assert client.get(f"/post/{tweet_id}").status_code == 404
