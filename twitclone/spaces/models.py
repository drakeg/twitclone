"""Data model for persistent Ripple community/topic spaces."""

from datetime import UTC, datetime

from twitclone.extensions import db


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class Space(db.Model):
    __tablename__ = "space"
    __table_args__ = (
        db.UniqueConstraint("slug", name="uq_space_slug"),
        db.CheckConstraint("visibility in ('public')", name="ck_space_visibility"),
    )

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    visibility = db.Column(db.String(20), nullable=False, default="public", server_default="public")
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)

    owner = db.relationship("User", foreign_keys=[owner_id])
    memberships = db.relationship(
        "SpaceMembership",
        back_populates="space",
        cascade="all, delete-orphan",
        lazy=True,
    )
    posts = db.relationship(
        "SpacePost",
        back_populates="space",
        cascade="all, delete-orphan",
        lazy=True,
    )
    resource_links = db.relationship(
        "SpaceResource",
        back_populates="space",
        cascade="all, delete-orphan",
        lazy=True,
    )


class SpaceMembership(db.Model):
    __tablename__ = "space_membership"
    __table_args__ = (
        db.UniqueConstraint("space_id", "user_id", name="uq_space_membership_space_user"),
        db.CheckConstraint("role in ('owner', 'moderator', 'member')", name="ck_space_membership_role"),
    )

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("space.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="member", server_default="member")
    joined_at = db.Column(db.DateTime, nullable=False, default=_utcnow)

    space = db.relationship("Space", back_populates="memberships")
    user = db.relationship("User")


class SpacePost(db.Model):
    __tablename__ = "space_post"
    __table_args__ = (db.UniqueConstraint("tweet_id", name="uq_space_post_tweet"),)

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("space.id", ondelete="CASCADE"), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey("tweet.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    is_hidden = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    hidden_at = db.Column(db.DateTime, nullable=True)
    hidden_by_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    hidden_reason = db.Column(db.String(500), nullable=True)

    space = db.relationship("Space", back_populates="posts")
    tweet = db.relationship("Tweet")
    hidden_by = db.relationship("User", foreign_keys=[hidden_by_id])


class SpaceResource(db.Model):
    __tablename__ = "space_resource"
    __table_args__ = (
        db.UniqueConstraint("space_id", "resource_id", name="uq_space_resource_space_resource"),
    )

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("space.id", ondelete="CASCADE"), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey("resource.id", ondelete="CASCADE"), nullable=False)
    linked_by_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    linked_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    is_hidden = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    hidden_at = db.Column(db.DateTime, nullable=True)
    hidden_by_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    hidden_reason = db.Column(db.String(500), nullable=True)

    space = db.relationship("Space", back_populates="resource_links")
    resource = db.relationship("Resource")
    linked_by = db.relationship("User", foreign_keys=[linked_by_id])
    hidden_by = db.relationship("User", foreign_keys=[hidden_by_id])


class SpaceModerationAction(db.Model):
    __tablename__ = "space_moderation_action"
    __table_args__ = (
        db.CheckConstraint(
            "action_type in ('hide_post', 'restore_post', 'hide_resource', 'restore_resource', 'promote_moderator', 'demote_moderator')",
            name="ck_space_moderation_action_type",
        ),
        db.CheckConstraint("target_type in ('post', 'resource', 'membership')", name="ck_space_moderation_target_type"),
    )

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("space.id", ondelete="CASCADE"), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    action_type = db.Column(db.String(40), nullable=False)
    target_type = db.Column(db.String(20), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    affected_user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    reason = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)

    space = db.relationship("Space")
    actor = db.relationship("User", foreign_keys=[actor_id])
    affected_user = db.relationship("User", foreign_keys=[affected_user_id])


class SpaceModerationAppeal(db.Model):
    __tablename__ = "space_moderation_appeal"
    __table_args__ = (
        db.UniqueConstraint("action_id", name="uq_space_moderation_appeal_action"),
        db.CheckConstraint("status in ('pending', 'approved', 'denied')", name="ck_space_moderation_appeal_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("space.id", ondelete="CASCADE"), nullable=False)
    action_id = db.Column(db.Integer, db.ForeignKey("space_moderation_action.id", ondelete="CASCADE"), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    rationale = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending", server_default="pending")
    submitted_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    resolution_note = db.Column(db.String(500), nullable=True)

    space = db.relationship("Space")
    action = db.relationship("SpaceModerationAction")
    requester = db.relationship("User", foreign_keys=[requester_id])
    resolved_by = db.relationship("User", foreign_keys=[resolved_by_id])


__all__ = [
    "Space",
    "SpaceMembership",
    "SpacePost",
    "SpaceResource",
    "SpaceModerationAction",
    "SpaceModerationAppeal",
]
