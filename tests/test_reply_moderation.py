"""Sprint 14 Story 14.4 reply contribution/reporting/moderation coverage."""

from twitclone.contribution_models import ConstructiveContribution
from twitclone.extensions import db
from twitclone.models import Tweet, User
from twitclone.reply_models import Reply, ReplyContribution, ReplyReport


def _user(app, username, *, admin=False):
    with app.app_context():
        user = User(
            username=username,
            email=f"{username}@example.com",
            password="hash",
            is_admin=admin,
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _thread(app):
    author_id = _user(app, "reply_mod_author")
    replier_id = _user(app, "reply_mod_writer")
    with app.app_context():
        tweet = Tweet(content="moderated root", user_id=author_id)
        db.session.add(tweet)
        db.session.flush()
        reply = Reply(tweet_id=tweet.id, user_id=replier_id, content="useful reply")
        db.session.add(reply)
        db.session.commit()
        return tweet.id, reply.id, author_id, replier_id


def test_reply_contribution_toggle_is_separate_from_post_contribution(client, app):
    tweet_id, reply_id, viewer_id, _ = _thread(app)
    _login(client, viewer_id)

    response = client.post(f"/post/{tweet_id}/reply/{reply_id}/contribution/helpful")
    assert response.status_code == 302
    with app.app_context():
        row = ReplyContribution.query.one()
        assert row.reply_id == reply_id
        assert row.signal == "helpful"
        assert ConstructiveContribution.query.count() == 0

    response = client.post(f"/post/{tweet_id}/reply/{reply_id}/contribution/helpful")
    assert response.status_code == 302
    with app.app_context():
        assert ReplyContribution.query.count() == 0


def test_reply_author_cannot_self_signal(client, app):
    tweet_id, reply_id, _, replier_id = _thread(app)
    _login(client, replier_id)
    response = client.post(f"/post/{tweet_id}/reply/{reply_id}/contribution/thoughtful")
    assert response.status_code == 302
    with app.app_context():
        assert ReplyContribution.query.count() == 0


def test_reply_report_is_attributable_and_duplicate_safe(client, app):
    tweet_id, reply_id, reporter_id, replier_id = _thread(app)
    _login(client, reporter_id)

    response = client.post(
        f"/post/{tweet_id}/reply/{reply_id}/report",
        data={"category": "abuse", "details": "personal attack"},
    )
    assert response.status_code == 302
    with app.app_context():
        report = ReplyReport.query.one()
        assert report.reporter_id == reporter_id
        assert report.author_id == replier_id
        assert report.reply_id == reply_id
        assert report.status == "pending"

    duplicate = client.post(
        f"/post/{tweet_id}/reply/{reply_id}/report",
        data={"category": "spam"},
    )
    assert duplicate.status_code == 302
    with app.app_context():
        assert ReplyReport.query.count() == 1


def test_reply_report_appears_in_admin_queue_and_removal_hides_reply(client, app):
    tweet_id, reply_id, reporter_id, replier_id = _thread(app)
    admin_id = _user(app, "reply_mod_admin", admin=True)
    with app.app_context():
        report = ReplyReport(
            reporter_id=reporter_id,
            author_id=replier_id,
            reply_id=reply_id,
            category="abuse",
        )
        db.session.add(report)
        db.session.commit()
        report_id = report.id

    _login(client, admin_id)
    queue = client.get("/admin/moderation?content_type=reply")
    assert queue.status_code == 200
    assert b"useful reply" in queue.data
    assert b"Reply" in queue.data

    response = client.post(
        f"/admin/moderation/reply/{report_id}",
        data={"action": "remove", "resolution_notes": "violates standards"},
    )
    assert response.status_code == 302
    with app.app_context():
        reply = db.session.get(Reply, reply_id)
        report = db.session.get(ReplyReport, report_id)
        assert reply.is_removed is True
        assert reply.removed_by_id == admin_id
        assert reply.removal_reason == "violates standards"
        assert report.status == "removed"

    thread = client.get(f"/post/{tweet_id}/thread")
    assert thread.status_code == 200
    assert b"useful reply" not in thread.data


def test_reply_report_dismissal_preserves_reply(client, app):
    tweet_id, reply_id, reporter_id, replier_id = _thread(app)
    admin_id = _user(app, "reply_mod_dismiss_admin", admin=True)
    with app.app_context():
        report = ReplyReport(
            reporter_id=reporter_id,
            author_id=replier_id,
            reply_id=reply_id,
            category="other",
        )
        db.session.add(report)
        db.session.commit()
        report_id = report.id

    _login(client, admin_id)
    response = client.post(
        f"/admin/moderation/reply/{report_id}",
        data={"action": "dismiss", "resolution_notes": "no violation"},
    )
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(ReplyReport, report_id).status == "dismissed"
        assert db.session.get(Reply, reply_id).is_removed is False
