"""Regression coverage for appeals of published community context."""

from twitclone.community.routes import COMMUNITY_GUIDELINES_VERSION
from twitclone.extensions import db
from twitclone.fact_context_models import FactContextAppeal, FactContextSubmission
from twitclone.models import Tweet, User


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


def _approved_context(app):
    author_id = _user(app, "author")
    submitter_id = _user(app, "checker")
    with app.app_context():
        tweet = Tweet(content="Original claim", user_id=author_id)
        db.session.add(tweet)
        db.session.flush()
        submission = FactContextSubmission(
            tweet_id=tweet.id,
            submitter_id=submitter_id,
            claim="Claim under review",
            context="Original published context",
            source_url="https://example.com/original",
            status="approved",
            outcome="context",
        )
        db.session.add(submission)
        db.session.commit()
        return tweet.id, submission.id


def test_user_can_appeal_published_context_without_hiding_it(client, app):
    tweet_id, submission_id = _approved_context(app)
    appellant_id = _user(app, "appellant")
    _login(client, appellant_id)

    response = client.post(
        f"/community-context/{submission_id}/appeal",
        data={
            "reason": "The source is outdated.",
            "source_url": "https://example.com/new-evidence",
            "proposed_context": "Updated context",
        },
    )
    assert response.status_code == 302
    with app.app_context():
        appeal = FactContextAppeal.query.one()
        assert appeal.status == "pending"
        assert appeal.appellant_id == appellant_id
        assert db.session.get(FactContextSubmission, submission_id).is_public is True

    detail = client.get(f"/post/{tweet_id}")
    assert b"Original published context" in detail.data


def test_admin_revision_changes_public_presentation_but_keeps_original(client, app):
    tweet_id, submission_id = _approved_context(app)
    appellant_id = _user(app, "appellant")
    admin_id = _user(app, "moderator", admin=True)
    with app.app_context():
        appeal = FactContextAppeal(
            submission_id=submission_id,
            appellant_id=appellant_id,
            reason="New evidence changes the context.",
        )
        db.session.add(appeal)
        db.session.commit()
        appeal_id = appeal.id

    _login(client, admin_id)
    response = client.post(
        f"/admin/fact-context-appeals/{appeal_id}",
        data={
            "action": "revise",
            "resolved_outcome": "outdated",
            "resolved_context": "Revised published context",
            "resolved_source_url": "https://example.com/revised",
            "resolution_notes": "Newer evidence supersedes the original source.",
        },
    )
    assert response.status_code == 302

    with app.app_context():
        submission = db.session.get(FactContextSubmission, submission_id)
        assert submission.context == "Original published context"
        assert submission.public_context == "Revised published context"
        assert submission.public_outcome == "outdated"
        assert submission.was_revised_after_appeal is True

    detail = client.get(f"/post/{tweet_id}")
    assert b"Revised published context" in detail.data
    assert b"Revised after an appeal review" in detail.data


def test_admin_withdrawal_stops_public_display_without_deleting_history(client, app):
    tweet_id, submission_id = _approved_context(app)
    appellant_id = _user(app, "appellant")
    admin_id = _user(app, "moderator", admin=True)
    with app.app_context():
        appeal = FactContextAppeal(
            submission_id=submission_id,
            appellant_id=appellant_id,
            reason="The evidence does not support publication.",
        )
        db.session.add(appeal)
        db.session.commit()
        appeal_id = appeal.id

    _login(client, admin_id)
    response = client.post(
        f"/admin/fact-context-appeals/{appeal_id}",
        data={"action": "withdraw", "resolution_notes": "Context is no longer supported."},
    )
    assert response.status_code == 302

    with app.app_context():
        submission = db.session.get(FactContextSubmission, submission_id)
        assert submission.status == "approved"
        assert submission.context == "Original published context"
        assert submission.is_public is False
        assert FactContextAppeal.query.count() == 1

    detail = client.get(f"/post/{tweet_id}")
    assert b"Original published context" not in detail.data


def test_same_user_cannot_create_duplicate_pending_appeal(client, app):
    _, submission_id = _approved_context(app)
    appellant_id = _user(app, "appellant")
    with app.app_context():
        db.session.add(FactContextAppeal(
            submission_id=submission_id,
            appellant_id=appellant_id,
            reason="Existing pending appeal",
        ))
        db.session.commit()

    _login(client, appellant_id)
    response = client.get(f"/community-context/{submission_id}/appeal", follow_redirects=True)
    assert b"already have a pending appeal" in response.data
    with app.app_context():
        assert FactContextAppeal.query.count() == 1
