"""Durable collaborative resource models for Sprint 11."""

from datetime import UTC, datetime

from twitclone.extensions import db


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class Resource(db.Model):
    __tablename__ = "resource"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    current_revision_id = db.Column(db.Integer, nullable=True)
    is_removed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    owner = db.relationship("User", backref=db.backref("resources", lazy=True))
    revisions = db.relationship(
        "ResourceRevision",
        backref="resource",
        lazy=True,
        cascade="all, delete-orphan",
        foreign_keys="ResourceRevision.resource_id",
        order_by="ResourceRevision.revision_number.asc()",
    )

    @property
    def current_revision(self):
        if self.current_revision_id is None:
            return self.revisions[-1] if self.revisions else None
        return next((revision for revision in self.revisions if revision.id == self.current_revision_id), None)


class ResourceRevision(db.Model):
    __tablename__ = "resource_revision"
    __table_args__ = (
        db.UniqueConstraint("resource_id", "revision_number", name="uq_resource_revision_number"),
    )

    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("resource.id", ondelete="CASCADE"), nullable=False)
    editor_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    revision_number = db.Column(db.Integer, nullable=False)
    body = db.Column(db.Text, nullable=False)
    source_url = db.Column(db.String(1000), nullable=True)
    change_note = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)

    editor = db.relationship("User", backref=db.backref("resource_revisions", lazy=True))


class ResourceTopic(db.Model):
    __tablename__ = "resource_topic"
    __table_args__ = (
        db.UniqueConstraint("resource_id", "topic_id", name="uq_resource_topic_resource_topic"),
    )

    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("resource.id", ondelete="CASCADE"), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey("topic.id", ondelete="CASCADE"), nullable=False)

    resource = db.relationship("Resource", backref=db.backref("topic_associations", lazy=True, cascade="all, delete-orphan"))
    topic = db.relationship("Topic", backref=db.backref("resource_associations", lazy=True))


__all__ = ["Resource", "ResourceRevision", "ResourceTopic"]
