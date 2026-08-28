"""Collaborative resource creation and browsing routes."""

from difflib import ndiff
from urllib.parse import urlparse

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.extensions import db
from twitclone.resource_models import Resource, ResourceRevision, ResourceTopic
from twitclone.resources import resources_blueprint
from twitclone.topic_models import Topic, explicit_topic_values


def _valid_source_url(value):
    if not value:
        return True
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _associate_resource_topics(resource, raw_topics):
    for name, slug in explicit_topic_values(raw_topics):
        topic = Topic.query.filter_by(slug=slug).first()
        if topic is None:
            topic = Topic(name=name, slug=slug)
            db.session.add(topic)
            db.session.flush()
        db.session.add(ResourceTopic(resource_id=resource.id, topic_id=topic.id))


def _can_publish_revision(resource, user):
    """Keep publication authority explicit until broader collaboration is reviewed."""
    return bool(user.is_authenticated and (user.id == resource.owner_id or user.is_admin))


def _revision_changes(previous, revision):
    if previous is None:
        return []
    changes = []
    for line in ndiff(previous.body.splitlines(), revision.body.splitlines()):
        if line.startswith("- "):
            changes.append(("removed", line[2:]))
        elif line.startswith("+ "):
            changes.append(("added", line[2:]))
    return changes


def index():
    resources = Resource.query.filter_by(is_removed=False).order_by(Resource.updated_at.desc()).all()
    return render_template("resources/index.html", resources=resources)


@login_required
def create_resource():
    if request.method == "GET":
        return render_template("resources/create.html")

    title = " ".join((request.form.get("title") or "").split())
    body = (request.form.get("body") or "").strip()
    source_url = (request.form.get("source_url") or "").strip() or None
    topics = request.form.get("topics") or ""

    if not title or len(title) > 160:
        flash("Give the resource a title between 1 and 160 characters.", "danger")
        return render_template("resources/create.html"), 400
    if not body:
        flash("Resource content is required.", "danger")
        return render_template("resources/create.html"), 400
    if not _valid_source_url(source_url):
        flash("Source links must use http:// or https://.", "danger")
        return render_template("resources/create.html"), 400

    resource = Resource(owner_id=current_user.id, title=title)
    db.session.add(resource)
    db.session.flush()
    revision = ResourceRevision(
        resource_id=resource.id,
        editor_id=current_user.id,
        revision_number=1,
        body=body,
        source_url=source_url,
        change_note="Initial version",
    )
    db.session.add(revision)
    db.session.flush()
    resource.current_revision_id = revision.id
    _associate_resource_topics(resource, topics)
    db.session.commit()
    flash("Resource published with revision history started.", "success")
    return redirect(url_for("resources.resource_detail", resource_id=resource.id))


def resource_detail(resource_id):
    resource = db.get_or_404(Resource, resource_id)
    if resource.is_removed:
        abort(404)
    return render_template(
        "resources/detail.html",
        resource=resource,
        can_publish_revision=_can_publish_revision(resource, current_user),
    )


def resource_revision(resource_id, revision_number):
    resource = db.get_or_404(Resource, resource_id)
    if resource.is_removed:
        abort(404)
    revision = ResourceRevision.query.filter_by(
        resource_id=resource.id, revision_number=revision_number
    ).first_or_404()
    previous = ResourceRevision.query.filter_by(
        resource_id=resource.id, revision_number=revision_number - 1
    ).first()
    return render_template(
        "resources/revision.html",
        resource=resource,
        revision=revision,
        previous_revision=previous,
        changes=_revision_changes(previous, revision),
        is_current=resource.current_revision_id == revision.id,
    )


@login_required
def revise_resource(resource_id):
    resource = db.get_or_404(Resource, resource_id)
    if resource.is_removed:
        abort(404)
    if not _can_publish_revision(resource, current_user):
        abort(403)

    current = resource.current_revision
    if request.method == "GET":
        return render_template("resources/revise.html", resource=resource, current_revision=current)

    body = (request.form.get("body") or "").strip()
    source_url = (request.form.get("source_url") or "").strip() or None
    change_note = " ".join((request.form.get("change_note") or "").split())
    if not body:
        flash("Resource content is required.", "danger")
        return render_template("resources/revise.html", resource=resource, current_revision=current), 400
    if not change_note or len(change_note) > 300:
        flash("Describe the change in 1 to 300 characters.", "danger")
        return render_template("resources/revise.html", resource=resource, current_revision=current), 400
    if not _valid_source_url(source_url):
        flash("Source links must use http:// or https://.", "danger")
        return render_template("resources/revise.html", resource=resource, current_revision=current), 400

    next_number = max((revision.revision_number for revision in resource.revisions), default=0) + 1
    revision = ResourceRevision(
        resource_id=resource.id,
        editor_id=current_user.id,
        revision_number=next_number,
        body=body,
        source_url=source_url,
        change_note=change_note,
    )
    db.session.add(revision)
    db.session.flush()
    resource.current_revision_id = revision.id
    db.session.commit()
    flash(f"Revision {next_number} published with attribution preserved.", "success")
    return redirect(url_for("resources.resource_detail", resource_id=resource.id))


resources_blueprint.add_url_rule("/", endpoint="index", view_func=index)
resources_blueprint.add_url_rule(
    "/new", endpoint="create_resource", view_func=create_resource, methods=["GET", "POST"]
)
resources_blueprint.add_url_rule(
    "/<int:resource_id>", endpoint="resource_detail", view_func=resource_detail
)
resources_blueprint.add_url_rule(
    "/<int:resource_id>/revisions/<int:revision_number>",
    endpoint="resource_revision",
    view_func=resource_revision,
)
resources_blueprint.add_url_rule(
    "/<int:resource_id>/revise",
    endpoint="revise_resource",
    view_func=revise_resource,
    methods=["GET", "POST"],
)
