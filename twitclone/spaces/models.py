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


class SpaceMembership(db.Model):
    __tablename__ = "space_membership"
    __table_args__ = (
        db.UniqueConstraint("space_id", "user_id", name="uq_space_membership_space_user"),
        db.CheckConstraint("role in ('owner', 'member')", name="ck_space_membership_role"),
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

    space = db.relationship("Space", back_populates="posts")
    tweet = db.relationship("Tweet")


__all__ = ["Space", "SpaceMembership", "SpacePost"]
