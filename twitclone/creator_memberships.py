"""Creator membership offering foundation for Sprint 15.

Membership offerings describe optional supporter benefits only. This module does
not enroll supporters, process payments, grant entitlements, or affect organic
reach, reputation, verification, moderation, or safety behavior.
"""

from datetime import UTC, datetime

from twitclone.extensions import db

MAX_MEMBERSHIP_NAME_LENGTH = 80
MAX_MEMBERSHIP_DESCRIPTION_LENGTH = 280

MEMBERSHIP_BENEFITS = {
    "supporter_updates": "Supporter-only creator updates",
    "early_access": "Early access to creator-published material",
    "member_q_and_a": "Member Q&A participation",
    "downloadable_resources": "Creator-provided downloadable resources",
}


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class CreatorMembershipOffering(db.Model):
    __tablename__ = "creator_membership_offering"
    __table_args__ = (db.UniqueConstraint("user_id", name="uq_creator_membership_offering_user"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    name = db.Column(db.String(MAX_MEMBERSHIP_NAME_LENGTH), nullable=True)
    description = db.Column(db.String(MAX_MEMBERSHIP_DESCRIPTION_LENGTH), nullable=True)
    benefits = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    user = db.relationship("User", backref=db.backref("creator_membership_offering", uselist=False))

    @property
    def benefit_keys(self):
        return parse_benefit_keys(self.benefits)

    @property
    def benefit_labels(self):
        return [MEMBERSHIP_BENEFITS[key] for key in self.benefit_keys]


def normalized_membership_name(value):
    value = (value or "").strip()
    return value[:MAX_MEMBERSHIP_NAME_LENGTH] or None


def normalized_membership_description(value):
    value = (value or "").strip()
    return value[:MAX_MEMBERSHIP_DESCRIPTION_LENGTH] or None


def normalize_benefit_keys(values):
    normalized = []
    for value in values or []:
        key = (value or "").strip()
        if key in MEMBERSHIP_BENEFITS and key not in normalized:
            normalized.append(key)
    return normalized


def serialize_benefit_keys(values):
    return ",".join(normalize_benefit_keys(values)) or None


def parse_benefit_keys(value):
    return normalize_benefit_keys((value or "").split(","))


__all__ = [
    "CreatorMembershipOffering",
    "MAX_MEMBERSHIP_DESCRIPTION_LENGTH",
    "MAX_MEMBERSHIP_NAME_LENGTH",
    "MEMBERSHIP_BENEFITS",
    "normalize_benefit_keys",
    "normalized_membership_description",
    "normalized_membership_name",
    "parse_benefit_keys",
    "serialize_benefit_keys",
]
