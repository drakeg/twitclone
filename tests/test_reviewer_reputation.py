"""Regression coverage for transparent community reviewer reputation."""

from twitclone.community.routes import COMMUNITY_GUIDELINES_VERSION
from twitclone.extensions import db
from twitclone.fact_context_models import FactContextAssessment, FactContextSubmission
from twitclone.models import Tweet, User
from twitclone.reviewer_reputation import reviewer_reputation


def _user(app, username):
    with app.app_context():
        user = User(
            username=username,
            email=f"{username}@example.com",
            password="hash",
            community_guidelines_version=COMMUNITY_GUIDELINES_VERSION,
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _resolved_review(app, reviewer_id, index, *, assessment="context", outcome="context"):
    with app.app_context():
        author = User(username=f"author{index}", email=f"author{index}@example.com", password="hash")
        submitter = User(username=f"submitter{index}", email=f"submitter{index}@example.com", password="hash")
        db.session.add_all([author, submitter])
        db.session.flush()
        tweet = Tweet(content=f"Claim {index}", user_id=author.id)
        db.session.add(tweet)
        db.session.flush()
        submission = FactContextSubmission(
            tweet_id=tweet.id,
            submitter_id=submitter.id,
            claim=f"Claim {index}",
            context="Evidence-backed context",
            source_url="https://example.com/source",
            status="approved",
            outcome=outcome,
        )
        db.session.add(submission)
        db.session.flush()
        db.session.add(FactContextAssessment(
            submission_id=submission.id,
            reviewer_id=reviewer_id,
            assessment=assessment,
        ))
        db.session.commit()


def test_reputation_is_derived_from_resolved_outcomes(app):
    reviewer_id = _user(app, "reviewer")
    for index in range(1, 9):
        _resolved_review(
            app,
            reviewer_id,
            index,
            assessment="context" if index <= 6 else "disputed",
            outcome="context",
        )

    with app.app_context():
        reputation = reviewer_reputation(reviewer_id)
        assert reputation.total_assessments == 8
        assert reputation.resolved_assessments == 8
        assert reputation.aligned_assessments == 6
        assert reputation.agreement_rate == 75
        assert reputation.level == "established"
        assert reputation.label == "Established reviewer"


def test_pending_reviews_do_not_inflate_reputation(app):
    reviewer_id = _user(app, "reviewer")
    author_id = _user(app, "author")
    submitter_id = _user(app, "submitter")
    with app.app_context():
        tweet = Tweet(content="Pending claim", user_id=author_id)
        db.session.add(tweet)
        db.session.flush()
        submission = FactContextSubmission(
            tweet_id=tweet.id,
            submitter_id=submitter_id,
            claim="Pending claim",
            context="Context",
            source_url="https://example.com/source",
        )
        db.session.add(submission)
        db.session.flush()
        db.session.add(FactContextAssessment(
            submission_id=submission.id,
            reviewer_id=reviewer_id,
            assessment="context",
        ))
        db.session.commit()

        reputation = reviewer_reputation(reviewer_id)
        assert reputation.total_assessments == 1
        assert reputation.resolved_assessments == 0
        assert reputation.aligned_assessments == 0
        assert reputation.agreement_rate is None
        assert reputation.level == "new"


def test_review_queue_explains_reputation_without_vote_weight(client, app):
    reviewer_id = _user(app, "reviewer")
    _login(client, reviewer_id)

    response = client.get("/community-context")
    assert response.status_code == 200
    assert b"Your reviewer record" in response.data
    assert b"New reviewer" in response.data
    assert b"not based on followers, paid status, popularity, or political viewpoint" in response.data
    assert b"does not currently give your assessment extra voting weight" in response.data
