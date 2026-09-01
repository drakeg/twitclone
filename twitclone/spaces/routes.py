"""Routes for persistent community/topic spaces."""

import re
from datetime import UTC, datetime

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.extensions import db
from twitclone.models import Tweet
from twitclone.resource_models import Resource
from twitclone.spaces import spaces_blueprint
from twitclone.spaces.models import (
    Space,
    SpaceMembership,
    SpaceModerationAction,
    SpaceModerationAppeal,
    SpacePost,
    SpaceResource,
)
from twitclone.timeline.validation import validate_post_content

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


def _slugify(value):
    slug = _SLUG_RE.sub("-", (value or "").strip().casefold()).strip("-")
    return slug[:80]


def _membership(space):
    if not current_user.is_authenticated:
        return None
    return SpaceMembership.query.filter_by(space_id=space.id, user_id=current_user.id).first()


def _can_moderate(membership):
    return membership is not None and membership.role in {"owner", "moderator"}


def _visible_space_posts(space):
    return (
        SpacePost.query.join(SpacePost.tweet)
        .filter(
            SpacePost.space_id == space.id,
            SpacePost.is_hidden.is_(False),
            Tweet.is_removed.is_(False),
        )
        .order_by(Tweet.timestamp.desc(), SpacePost.id.desc())
        .all()
    )


def _visible_space_resources(space):
    return (
        SpaceResource.query.join(SpaceResource.resource)
        .filter(
            SpaceResource.space_id == space.id,
            SpaceResource.is_hidden.is_(False),
            Resource.is_removed.is_(False),
        )
        .order_by(SpaceResource.linked_at.desc(), SpaceResource.id.desc())
        .all()
    )


def _resource_candidates(space):
    linked_ids = {
        row.resource_id for row in SpaceResource.query.filter_by(space_id=space.id).all()
    }
    query = Resource.query.filter_by(is_removed=False)
    if linked_ids:
        query = query.filter(~Resource.id.in_(linked_ids))
    return query.order_by(Resource.updated_at.desc(), Resource.id.desc()).limit(100).all()


def _audit(space, *, action_type, target_type, target_id, affected_user_id, reason):
    action = SpaceModerationAction(
        space_id=space.id,
        actor_id=current_user.id,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        affected_user_id=affected_user_id,
        reason=reason,
    )
    db.session.add(action)
    return action


def _require_reason():
    reason = (request.form.get("reason") or "").strip()
    if not reason or len(reason) > 500:
        abort(400, description="A moderation reason between 1 and 500 characters is required.")
    return reason


@spaces_blueprint.get("/")
def index():
    spaces = Space.query.order_by(Space.name.asc(), Space.id.asc()).all()
    memberships = set()
    if current_user.is_authenticated:
        memberships = {
            row.space_id
            for row in SpaceMembership.query.filter_by(user_id=current_user.id).all()
        }
    return render_template("spaces/index.html", spaces=spaces, memberships=memberships)


@spaces_blueprint.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        slug = _slugify(request.form.get("slug") or name)
        if not name or len(name) > 120:
            flash("Space name must be between 1 and 120 characters.", "danger")
            return render_template("spaces/create.html"), 400
        if not description or len(description) > 500:
            flash("Space description must be between 1 and 500 characters.", "danger")
            return render_template("spaces/create.html"), 400
        if not slug:
            flash("Choose a name that produces a usable space URL.", "danger")
            return render_template("spaces/create.html"), 400
        if Space.query.filter_by(slug=slug).first() is not None:
            flash("That space URL is already in use.", "danger")
            return render_template("spaces/create.html"), 400
        space = Space(name=name, slug=slug, description=description, owner_id=current_user.id)
        db.session.add(space)
        db.session.flush()
        db.session.add(SpaceMembership(space_id=space.id, user_id=current_user.id, role="owner"))
        db.session.commit()
        flash("Space created.", "success")
        return redirect(url_for("spaces.detail", slug=space.slug))
    return render_template("spaces/create.html")


@spaces_blueprint.get("/<slug>")
def detail(slug):
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    member_count = SpaceMembership.query.filter_by(space_id=space.id).count()
    member_rows = (
        SpaceMembership.query.filter_by(space_id=space.id)
        .order_by(SpaceMembership.role.asc(), SpaceMembership.joined_at.asc(), SpaceMembership.id.asc())
        .all()
    ) if membership and membership.role == "owner" else []
    moderation_history = []
    pending_appeals = []
    my_moderation = []
    if _can_moderate(membership):
        moderation_history = (
            SpaceModerationAction.query.filter_by(space_id=space.id)
            .order_by(SpaceModerationAction.created_at.desc(), SpaceModerationAction.id.desc())
            .limit(50)
            .all()
        )
        pending_appeals = (
            SpaceModerationAppeal.query.filter_by(space_id=space.id, status="pending")
            .order_by(SpaceModerationAppeal.submitted_at.asc(), SpaceModerationAppeal.id.asc())
            .all()
        )
    if current_user.is_authenticated:
        my_moderation = (
            SpaceModerationAction.query.filter_by(space_id=space.id, affected_user_id=current_user.id)
            .filter(SpaceModerationAction.action_type.in_(["hide_post", "hide_resource"]))
            .order_by(SpaceModerationAction.created_at.desc(), SpaceModerationAction.id.desc())
            .limit(20)
            .all()
        )
    appeals_by_action = {}
    if my_moderation:
        appeals_by_action = {
            appeal.action_id: appeal
            for appeal in SpaceModerationAppeal.query.filter(
                SpaceModerationAppeal.action_id.in_([action.id for action in my_moderation])
            ).all()
        }
    return render_template(
        "spaces/detail.html",
        space=space,
        membership=membership,
        member_count=member_count,
        member_rows=member_rows,
        space_posts=_visible_space_posts(space),
        space_resources=_visible_space_resources(space),
        resource_candidates=_resource_candidates(space) if membership else [],
        moderation_history=moderation_history,
        pending_appeals=pending_appeals,
        my_moderation=my_moderation,
        appeals_by_action=appeals_by_action,
        can_moderate=_can_moderate(membership),
    )


@spaces_blueprint.post("/<slug>/posts")
@login_required
def publish_post(slug):
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    if membership is None:
        abort(403)
    content = request.form.get("content")
    validation_error = validate_post_content(content, post_type="Space post")
    if validation_error:
        flash(validation_error, "danger")
        return redirect(url_for("spaces.detail", slug=space.slug))
    tweet = Tweet(content=content, user_id=current_user.id)
    db.session.add(tweet)
    db.session.flush()
    db.session.add(SpacePost(space_id=space.id, tweet_id=tweet.id))
    db.session.commit()
    flash(f"Posted in {space.name}.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/resources")
@login_required
def link_resource(slug):
    space = Space.query.filter_by(slug=slug).first_or_404()
    if _membership(space) is None:
        abort(403)
    resource_id = request.form.get("resource_id", type=int)
    resource = db.session.get(Resource, resource_id) if resource_id else None
    if resource is None or resource.is_removed:
        abort(404)
    existing = SpaceResource.query.filter_by(space_id=space.id, resource_id=resource.id).first()
    if existing is None:
        db.session.add(
            SpaceResource(
                space_id=space.id,
                resource_id=resource.id,
                linked_by_id=current_user.id,
            )
        )
        db.session.commit()
        flash(f"Added {resource.title} to {space.name} knowledge.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/resources/<int:resource_id>/unlink")
@login_required
def unlink_resource(slug, resource_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    if _membership(space) is None:
        abort(403)
    link = SpaceResource.query.filter_by(space_id=space.id, resource_id=resource_id).first_or_404()
    if link.linked_by_id != current_user.id:
        abort(403)
    db.session.delete(link)
    db.session.commit()
    flash("Resource removed from this space's knowledge list. The resource itself was not deleted.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/members/<int:user_id>/role")
@login_required
def set_member_role(slug, user_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    if membership is None or membership.role != "owner":
        abort(403)
    target = SpaceMembership.query.filter_by(space_id=space.id, user_id=user_id).first_or_404()
    if target.role == "owner" or target.user_id == space.owner_id:
        abort(400)
    role = (request.form.get("role") or "").strip().lower()
    if role not in {"member", "moderator"}:
        abort(400)
    if target.role != role:
        old_role = target.role
        target.role = role
        action_type = "promote_moderator" if role == "moderator" else "demote_moderator"
        _audit(
            space,
            action_type=action_type,
            target_type="membership",
            target_id=target.id,
            affected_user_id=target.user_id,
            reason=f"Owner changed role from {old_role} to {role}.",
        )
        db.session.commit()
        flash(f"@{target.user.username} is now a {role}.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/posts/<int:space_post_id>/hide")
@login_required
def hide_post(slug, space_post_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    if not _can_moderate(_membership(space)):
        abort(403)
    row = SpacePost.query.filter_by(id=space_post_id, space_id=space.id).first_or_404()
    if row.is_hidden:
        return redirect(url_for("spaces.detail", slug=space.slug))
    reason = _require_reason()
    row.is_hidden = True
    row.hidden_at = _utcnow()
    row.hidden_by_id = current_user.id
    row.hidden_reason = reason
    _audit(
        space,
        action_type="hide_post",
        target_type="post",
        target_id=row.id,
        affected_user_id=row.tweet.user_id,
        reason=reason,
    )
    db.session.commit()
    flash("Post hidden from this space. The underlying post was not globally deleted.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/posts/<int:space_post_id>/restore")
@login_required
def restore_post(slug, space_post_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    if not _can_moderate(_membership(space)):
        abort(403)
    row = SpacePost.query.filter_by(id=space_post_id, space_id=space.id).first_or_404()
    if not row.is_hidden:
        return redirect(url_for("spaces.detail", slug=space.slug))
    reason = _require_reason()
    row.is_hidden = False
    row.hidden_at = None
    row.hidden_by_id = None
    row.hidden_reason = None
    _audit(
        space,
        action_type="restore_post",
        target_type="post",
        target_id=row.id,
        affected_user_id=row.tweet.user_id,
        reason=reason,
    )
    db.session.commit()
    flash("Post restored to this space.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/resources/<int:link_id>/hide")
@login_required
def hide_resource(slug, link_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    if not _can_moderate(_membership(space)):
        abort(403)
    link = SpaceResource.query.filter_by(id=link_id, space_id=space.id).first_or_404()
    if link.is_hidden:
        return redirect(url_for("spaces.detail", slug=space.slug))
    reason = _require_reason()
    link.is_hidden = True
    link.hidden_at = _utcnow()
    link.hidden_by_id = current_user.id
    link.hidden_reason = reason
    _audit(
        space,
        action_type="hide_resource",
        target_type="resource",
        target_id=link.id,
        affected_user_id=link.linked_by_id,
        reason=reason,
    )
    db.session.commit()
    flash("Resource link hidden from this space. The durable resource was not deleted.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/resources/<int:link_id>/restore")
@login_required
def restore_resource(slug, link_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    if not _can_moderate(_membership(space)):
        abort(403)
    link = SpaceResource.query.filter_by(id=link_id, space_id=space.id).first_or_404()
    if not link.is_hidden:
        return redirect(url_for("spaces.detail", slug=space.slug))
    reason = _require_reason()
    link.is_hidden = False
    link.hidden_at = None
    link.hidden_by_id = None
    link.hidden_reason = None
    _audit(
        space,
        action_type="restore_resource",
        target_type="resource",
        target_id=link.id,
        affected_user_id=link.linked_by_id,
        reason=reason,
    )
    db.session.commit()
    flash("Resource link restored to this space.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/moderation/<int:action_id>/appeal")
@login_required
def appeal_moderation(slug, action_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    action = SpaceModerationAction.query.filter_by(id=action_id, space_id=space.id).first_or_404()
    if action.action_type not in {"hide_post", "hide_resource"} or action.affected_user_id != current_user.id:
        abort(403)
    if SpaceModerationAppeal.query.filter_by(action_id=action.id).first() is not None:
        abort(400, description="This moderation action has already been appealed.")
    rationale = (request.form.get("rationale") or "").strip()
    if not rationale or len(rationale) > 500:
        abort(400, description="An appeal rationale between 1 and 500 characters is required.")
    db.session.add(
        SpaceModerationAppeal(
            space_id=space.id,
            action_id=action.id,
            requester_id=current_user.id,
            rationale=rationale,
        )
    )
    db.session.commit()
    flash("Appeal submitted to the space moderation team.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/appeals/<int:appeal_id>/resolve")
@login_required
def resolve_appeal(slug, appeal_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    if not _can_moderate(_membership(space)):
        abort(403)
    appeal = SpaceModerationAppeal.query.filter_by(id=appeal_id, space_id=space.id).first_or_404()
    if appeal.status != "pending":
        abort(400)
    decision = (request.form.get("decision") or "").strip().lower()
    note = (request.form.get("resolution_note") or "").strip()
    if decision not in {"approved", "denied"} or not note or len(note) > 500:
        abort(400)
    if appeal.requester_id == current_user.id:
        abort(403)

    if decision == "approved":
        action = appeal.action
        if action.action_type == "hide_post":
            row = db.session.get(SpacePost, action.target_id)
            if row is not None and row.space_id == space.id and row.is_hidden:
                row.is_hidden = False
                row.hidden_at = None
                row.hidden_by_id = None
                row.hidden_reason = None
                _audit(
                    space,
                    action_type="restore_post",
                    target_type="post",
                    target_id=row.id,
                    affected_user_id=action.affected_user_id,
                    reason=f"Appeal approved: {note}",
                )
        elif action.action_type == "hide_resource":
            link = db.session.get(SpaceResource, action.target_id)
            if link is not None and link.space_id == space.id and link.is_hidden:
                link.is_hidden = False
                link.hidden_at = None
                link.hidden_by_id = None
                link.hidden_reason = None
                _audit(
                    space,
                    action_type="restore_resource",
                    target_type="resource",
                    target_id=link.id,
                    affected_user_id=action.affected_user_id,
                    reason=f"Appeal approved: {note}",
                )

    appeal.status = decision
    appeal.resolved_at = _utcnow()
    appeal.resolved_by_id = current_user.id
    appeal.resolution_note = note
    db.session.commit()
    flash(f"Appeal {decision}.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/join")
@login_required
def join(slug):
    space = Space.query.filter_by(slug=slug).first_or_404()
    existing = _membership(space)
    if existing is None:
        db.session.add(SpaceMembership(space_id=space.id, user_id=current_user.id, role="member"))
        db.session.commit()
        flash(f"You joined {space.name}.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/leave")
@login_required
def leave(slug):
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    if membership is None:
        return redirect(url_for("spaces.detail", slug=space.slug))
    if membership.role == "owner" or space.owner_id == current_user.id:
        abort(400, description="A space owner cannot leave their space without transferring ownership.")
    db.session.delete(membership)
    db.session.commit()
    flash(f"You left {space.name}.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))
