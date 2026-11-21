"""Data model for persistent Ripple community/topic spaces."""

from datetime import UTC, datetime

from twitclone.extensions import db


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class Space(db.Model):
    __tablename__ = "space"
    __table_args__ = (
        db.UniqueConstraint("slug", name="uq_space_slug"),
        db.CheckConstraint("visibility in ('public', 'private')", name="ck_space_visibility"),
    )

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    visibility = db.Column(db.String(20), nullable=False, default="public", server_default="public")
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    archived_at = db.Column(db.DateTime, nullable=True)
    archived_by_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)

    owner = db.relationship("User", foreign_keys=[owner_id])
    archived_by = db.relationship("User", foreign_keys=[archived_by_id])
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
    announcements = db.relationship(
        "SpaceAnnouncement",
        back_populates="space",
        cascade="all, delete-orphan",
        lazy=True,
    )


class SpaceAnnouncement(db.Model):
    __tablename__ = "space_announcement"

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(
        db.Integer,
        db.ForeignKey("space.id", ondelete="CASCADE"),
        nullable=False,
    )
    author_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )
    title = db.Column(db.String(120), nullable=False)
    body = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    updated_at = db.Column(db.DateTime, nullable=True)
    is_withdrawn = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=db.false(),
    )
    withdrawn_at = db.Column(db.DateTime, nullable=True)
    withdrawn_by_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )

    space = db.relationship("Space", back_populates="announcements")
    author = db.relationship("User", foreign_keys=[author_id])
    withdrawn_by = db.relationship("User", foreign_keys=[withdrawn_by_id])
    actions = db.relationship(
        "SpaceAnnouncementAction",
        back_populates="announcement",
        cascade="all, delete-orphan",
        lazy=True,
    )


class SpaceAnnouncementAction(db.Model):
    __tablename__ = "space_announcement_action"
    __table_args__ = (
        db.CheckConstraint(
            "action_type in ('created', 'edited', 'withdrawn', 'restored')",
            name="ck_space_announcement_action_type",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(
        db.Integer,
        db.ForeignKey("space.id", ondelete="CASCADE"),
        nullable=False,
    )
    announcement_id = db.Column(
        db.Integer,
        db.ForeignKey("space_announcement.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )
    action_type = db.Column(db.String(20), nullable=False)
    previous_title = db.Column(db.String(120), nullable=True)
    new_title = db.Column(db.String(120), nullable=True)
    previous_body = db.Column(db.String(1000), nullable=True)
    new_body = db.Column(db.String(1000), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)

    space = db.relationship("Space")
    announcement = db.relationship("SpaceAnnouncement", back_populates="actions")
    actor = db.relationship("User", foreign_keys=[actor_id])


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
    pinned_at = db.Column(db.DateTime, nullable=True)
    pinned_by_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)

    space = db.relationship("Space", back_populates="posts")
    tweet = db.relationship("Tweet")
    hidden_by = db.relationship("User", foreign_keys=[hidden_by_id])
    pinned_by = db.relationship("User", foreign_keys=[pinned_by_id])


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


class SpaceLifecycleAction(db.Model):
    __tablename__ = "space_lifecycle_action"
    __table_args__ = (
        db.CheckConstraint(
            "action_type in ('settings_updated', 'archived', 'restored')",
            name="ck_space_lifecycle_action_type",
        ),
        db.CheckConstraint(
            "previous_visibility is null or previous_visibility in ('public', 'private')",
            name="ck_space_lifecycle_previous_visibility",
        ),
        db.CheckConstraint(
            "new_visibility is null or new_visibility in ('public', 'private')",
            name="ck_space_lifecycle_new_visibility",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("space.id", ondelete="CASCADE"), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    action_type = db.Column(db.String(40), nullable=False)
    previous_name = db.Column(db.String(120), nullable=True)
    new_name = db.Column(db.String(120), nullable=True)
    previous_visibility = db.Column(db.String(20), nullable=True)
    new_visibility = db.Column(db.String(20), nullable=True)
    details = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)

    space = db.relationship("Space")
    actor = db.relationship(
        "User",
        foreign_keys=[actor_id],
        backref=db.backref("space_lifecycle_actions", passive_deletes=False),
    )


class SpaceCurationAction(db.Model):
    __tablename__ = "space_curation_action"
    __table_args__ = (
        db.CheckConstraint(
            "action_type in ('pin_post', 'unpin_post')",
            name="ck_space_curation_action_type",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("space.id", ondelete="CASCADE"), nullable=False)
    space_post_id = db.Column(db.Integer, db.ForeignKey("space_post.id", ondelete="CASCADE"), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    action_type = db.Column(db.String(40), nullable=False)
    details = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)

    space = db.relationship("Space")
    space_post = db.relationship("SpacePost")
    actor = db.relationship(
        "User",
        foreign_keys=[actor_id],
        backref=db.backref("space_curation_actions", passive_deletes=False),
    )


class SpaceInvitation(db.Model):
    __tablename__ = "space_invitation"
    __table_args__ = (
        db.CheckConstraint(
            "status in ('pending', 'accepted', 'declined', 'canceled')",
            name="ck_space_invitation_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("space.id", ondelete="CASCADE"), nullable=False)
    invited_user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    invited_by_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending", server_default="pending")
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    responded_at = db.Column(db.DateTime, nullable=True)

    space = db.relationship("Space")
    invited_user = db.relationship("User", foreign_keys=[invited_user_id])
    invited_by = db.relationship("User", foreign_keys=[invited_by_id])


class SpaceMembershipRequest(db.Model):
    __tablename__ = "space_membership_request"
    __table_args__ = (
        db.CheckConstraint(
            "status in ('pending', 'approved', 'denied')",
            name="ck_space_membership_request_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("space.id", ondelete="CASCADE"), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending", server_default="pending")
    note = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)

    space = db.relationship("Space")
    requester = db.relationship("User", foreign_keys=[requester_id])
    resolved_by = db.relationship(
        "User",
        foreign_keys=[resolved_by_id],
        backref=db.backref("resolved_space_membership_requests", passive_deletes=False),
    )


class SpaceMembershipAction(db.Model):
    __tablename__ = "space_membership_action"
    __table_args__ = (
        db.CheckConstraint(
            "action_type in ('ownership_transferred', 'role_changed', 'member_removed')",
            name="ck_space_membership_action_type",
        ),
        db.CheckConstraint(
            "previous_role is null or previous_role in ('owner', 'moderator', 'member')",
            name="ck_space_membership_action_previous_role",
        ),
        db.CheckConstraint(
            "new_role is null or new_role in ('owner', 'moderator', 'member')",
            name="ck_space_membership_action_new_role",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.Integer, db.ForeignKey("space.id", ondelete="CASCADE"), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    affected_user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    action_type = db.Column(db.String(40), nullable=False)
    previous_role = db.Column(db.String(20), nullable=True)
    new_role = db.Column(db.String(20), nullable=True)
    details = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)

    space = db.relationship("Space")
    actor = db.relationship("User", foreign_keys=[actor_id])
    affected_user = db.relationship("User", foreign_keys=[affected_user_id])


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
    "SpaceAnnouncement",
    "SpaceAnnouncementAction",
    "SpaceInvitation",
    "SpaceLifecycleAction",
    "SpaceCurationAction",
    "SpaceMembership",
    "SpaceMembershipAction",
    "SpaceMembershipRequest",
    "SpacePost",
    "SpaceResource",
    "SpaceModerationAction",
    "SpaceModerationAppeal",
]
