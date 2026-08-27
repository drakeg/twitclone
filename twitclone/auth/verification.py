"""Email ownership verification state and helpers."""

from datetime import UTC, datetime

from twitclone.extensions import db


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class EmailVerificationStatus(db.Model):
    __tablename__ = "email_verification_status"

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)


def email_verification_status(user_id: int) -> EmailVerificationStatus | None:
    return db.session.get(EmailVerificationStatus, user_id)


def is_email_verified(user) -> bool:
    """Treat missing rows as verified for legacy/directly-created fixture accounts."""
    status = email_verification_status(user.id)
    return status is None or status.verified_at is not None


def mark_email_verified(user_id: int) -> EmailVerificationStatus:
    status = email_verification_status(user_id)
    if status is None:
        status = EmailVerificationStatus(user_id=user_id)
        db.session.add(status)
    if status.verified_at is None:
        status.verified_at = _utcnow()
    return status


def mark_email_unverified(user_id: int) -> EmailVerificationStatus:
    """Require ownership verification again after the registered email changes."""
    status = email_verification_status(user_id)
    if status is None:
        status = EmailVerificationStatus(user_id=user_id)
        db.session.add(status)
    status.verified_at = None
    return status
