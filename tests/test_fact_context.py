"""Regression coverage for Ripple community fact-check/context workflow."""

from twitclone.community.routes import COMMUNITY_GUIDELINES_VERSION
from twitclone.extensions import db
from twitclone.fact_context_models import FactContextSubmission
from twitclone.models import Notification, Tweet, User


def _user(app, username, *, admin=False):
    with app.app_context():
        user = User(
            username=username,
            email=f"{username}@example.com",
            password="hash",
            is_admin=admin,
            community_guidelines_version=COMMUNITY_GUIDELINES_VERSION,
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _tweet(app, author_id, content="The claim being checked"):
    with app.app_context():
        tweet = Tweet(content=content, user_id=author_id)
        db.session.add(tweet)
        db.session.commit()
        return tweet.id


def test_user_can_submit_evidence_backed_context_without_publication(client, app):
    author_id = _user(app, "author")
    submitter_id = _user(app, "checker")
    tweet_id = _tweet(app, author_id)
    _login(client, submitter_id)

    response = client.post(
        f"/post/{tweet_id}/context",
        data={
            "claim": "A specific factual claim",
            "context": "The cited source provides important correcting context.",
            "source_url": "https://example.com/evidence",
        },
    )

    assert response.status_code == 302
    with app.app_context():
        submission = FactContextSubmission.query.one()
        assert submission.status == "pending"
        assert submission.outcome is None
        assert Notification.query.filter_by(user_id=submitter_id).count() == 1

    detail = client.get(f"/post/{tweet_id}")
    assert b"Reviewed context attached" not in detail.data


def test_submission_requires_http_or_https_source(client, app):
    author_id = _user(app, "author")
    submitter_id = _user(app, "checker")
    tweet_id = _tweet(app, author_id)
    _login(client, submitter_id)

    response = client.post(
        f"/post/{tweet_id}/context",
        data={"claim": "Claim", "context": "Context", "source_url": "javascript:alert(1)"},
        follow_redirects=True,
    )

    assert b"valid http or https source URL" in response.data
    with app.app_context():
        assert FactContextSubmission.query.count() == 0


def test_admin_approval_publishes_reviewed_context_and_notifies_parties(client, app):
    author_id = _user(app, "author")
    submitter_id = _user(app, "checker")
    admin_id = _user(app, "moderator", admin=True)
    tweet_id = _tweet(app, author_id)
    with app.app_context():
        submission = FactContextSubmission(
            tweet_id=tweet_id,
            submitter_id=submitter_id,
            claim="Claim under review",
            context="Evidence-backed correction.",
            source_url="https://example.com/source",
        )
        db.session.add(submission)
        db.session.commit()
        submission_id = submission.id

    _login(client, admin_id)
    response = client.post(
        f"/admin/fact-context/{submission_id}",
        data={"action": "approve", "outcome": "correction", "review_notes": "Source supports this."},
    )
    assert response.status_code == 302

    with app.app_context():
        submission = db.session.get(FactContextSubmission, submission_id)
        assert submission.status == "approved"
        assert submission.outcome == "correction"
        assert submission.reviewed_by_id == admin_id
        assert Notification.query.filter_by(user_id=submitter_id).count() == 1
        assert Notification.query.filter_by(user_id=author_id).count() == 1

    detail = client.get(f"/post/{tweet_id}")
    assert b"Supported correction" in detail.data
    assert b"Evidence-backed correction" in detail.data
    assert b"Review supporting source" in detail.data


def test_admin_cannot_approve_without_outcome(client, app):
    author_id = _user(app, "author")
    submitter_id = _user(app, "checker")
    admin_id = _user(app, "moderator", admin=True)
    tweet_id = _tweet(app, author_id)
    with app.app_context():
        submission = FactContextSubmission(tweet_id=tweet_id, submitter_id=submitter_id, claim="Claim", context="Context", source_url="https://example.com")
        db.session.add(submission); db.session.commit(); submission_id = submission.id

    _login(client, admin_id)
    response = client.post(f"/admin/fact-context/{submission_id}", data={"action": "approve", "outcome": ""}, follow_redirects=True)
    assert b"Choose an accepted context outcome" in response.data
    with app.app_context():
        assert db.session.get(FactContextSubmission, submission_id).status == "pending"
