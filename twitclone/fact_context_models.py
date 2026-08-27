"""Persistence for evidence-backed community context attached to Ripple posts."""

from datetime import UTC, datetime

from twitclone.extensions import db


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class FactContextSubmission(db.Model):
    __tablename__ = "fact_context_submission"
    __table_args__ = (
        db.CheckConstraint(
            "status in ('pending', 'approved', 'rejected')",
            name="ck_fact_context_submission_status",
        ),
        db.CheckConstraint(
            "outcome is null or outcome in ('context', 'disputed', 'outdated', 'correction')",
            name="ck_fact_context_submission_outcome",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.Integer, db.ForeignKey("tweet.id", ondelete="CASCADE"), nullable=False)
    submitter_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    claim = db.Column(db.String(300), nullable=False)
    context = db.Column(db.Text, nullable=False)
    source_url = db.Column(db.String(1000), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending", server_default="pending")
    outcome = db.Column(db.String(20), nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    review_notes = db.Column(db.Text, nullable=True)

    tweet = db.relationship("Tweet", backref=db.backref("fact_context_submissions", cascade="all, delete-orphan"))
    submitter = db.relationship("User", foreign_keys=[submitter_id])
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])


__all__ = ["FactContextSubmission"]
