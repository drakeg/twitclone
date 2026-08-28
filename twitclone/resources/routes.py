"""Collaborative resource creation and browsing routes."""

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


@resources_blueprint.record_once
def register_resource_routes(state):
    state.app.add_url_rule("/", endpoint="index", view_func=index)
    state.app.add_url_rule("/new", endpoint="create_resource", view_func=create_resource, methods=["GET", "POST"])
    state.app.add_url_rule("/<int:resource_id>", endpoint="resource_detail", view_func=resource_detail)
    state.app.add_url_rule("/<int:resource_id>/revise", endpoint="revise_resource", view_func=revise_resource, methods=["GET", "POST"])
