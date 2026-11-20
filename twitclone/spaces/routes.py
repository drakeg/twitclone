"""Routes for persistent community/topic spaces."""

import re
from datetime import UTC, datetime, timedelta

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.extensions import db
from twitclone.models import Notification, Tweet, User
from twitclone.resource_models import Resource
from twitclone.spaces import spaces_blueprint
from twitclone.spaces.models import (
    Space,
    SpaceInvitation,
    SpaceMembership,
    SpaceMembershipAction,
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


def _can_view_space(space, membership=None):
    if space.visibility == "public":
        return True
    if membership is None:
        membership = _membership(space)
    return membership is not None


def _require_space_visibility(space, membership=None):
    if not _can_view_space(space, membership):
        abort(404)


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


def _audit_membership(
    space,
    *,
    action_type,
    affected_user_id,
    previous_role=None,
    new_role=None,
    details=None,
):
    action = SpaceMembershipAction(
        space_id=space.id,
        actor_id=current_user.id,
        affected_user_id=affected_user_id,
        action_type=action_type,
        previous_role=previous_role,
        new_role=new_role,
        details=details,
    )
    db.session.add(action)
    return action


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
    memberships = set()
    if current_user.is_authenticated:
        memberships = {
            row.space_id
            for row in SpaceMembership.query.filter_by(user_id=current_user.id).all()
        }
    spaces = (
        Space.query.filter(
            db.or_(
                Space.visibility == "public",
                Space.id.in_(memberships) if memberships else db.false(),
            )
        )
        .order_by(Space.name.asc(), Space.id.asc())
        .all()
    )
    return render_template("spaces/index.html", spaces=spaces, memberships=memberships)


@spaces_blueprint.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        slug = _slugify(request.form.get("slug") or name)
        visibility = (request.form.get("visibility") or "public").strip().lower()
        if not name or len(name) > 120:
            flash("Space name must be between 1 and 120 characters.", "danger")
            return render_template("spaces/create.html"), 400
        if not description or len(description) > 500:
            flash("Space description must be between 1 and 500 characters.", "danger")
            return render_template("spaces/create.html"), 400
        if not slug:
            flash("Choose a name that produces a usable space URL.", "danger")
            return render_template("spaces/create.html"), 400
        if visibility not in {"public", "private"}:
            flash("Choose a valid space visibility.", "danger")
            return render_template("spaces/create.html"), 400
        if Space.query.filter_by(slug=slug).first() is not None:
            flash("That space URL is already in use.", "danger")
            return render_template("spaces/create.html"), 400
        space = Space(
            name=name,
            slug=slug,
            description=description,
            owner_id=current_user.id,
            visibility=visibility,
        )
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
    _require_space_visibility(space, membership)
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





@spaces_blueprint.route("/<slug>/settings", methods=["GET", "POST"])
@login_required
def settings(slug):
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    if membership is None or membership.role != "owner" or space.owner_id != current_user.id:
        abort(403)

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        visibility = (request.form.get("visibility") or "").strip().lower()

        errors = []
        if not name or len(name) > 120:
            errors.append("Space name must be between 1 and 120 characters.")
        if not description or len(description) > 500:
            errors.append("Space description must be between 1 and 500 characters.")
        if visibility not in {"public", "private"}:
            errors.append("Choose a valid space visibility.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("spaces/settings.html", space=space), 400

        space.name = name
        space.description = description
        space.visibility = visibility
        db.session.commit()
        flash("Space settings updated.", "success")
        return redirect(url_for("spaces.detail", slug=space.slug))

    return render_template("spaces/settings.html", space=space)


@spaces_blueprint.get("/<slug>/operator")
@login_required
def operator_dashboard(slug):
    """Read-only operating view for space owners and moderators."""
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    if not _can_moderate(membership):
        abort(403)

    cutoff = _utcnow() - timedelta(days=30)
    member_count = SpaceMembership.query.filter_by(space_id=space.id).count()
    moderator_count = (
        SpaceMembership.query.filter(
            SpaceMembership.space_id == space.id,
            SpaceMembership.role.in_(["owner", "moderator"]),
        ).count()
    )
    new_members_30d = (
        SpaceMembership.query.filter(
            SpaceMembership.space_id == space.id,
            SpaceMembership.joined_at >= cutoff,
        ).count()
    )
    posts_30d = (
        SpacePost.query.join(SpacePost.tweet)
        .filter(
            SpacePost.space_id == space.id,
            SpacePost.created_at >= cutoff,
            SpacePost.is_hidden.is_(False),
            Tweet.is_removed.is_(False),
        )
        .count()
    )
    resources_30d = (
        SpaceResource.query.join(SpaceResource.resource)
        .filter(
            SpaceResource.space_id == space.id,
            SpaceResource.linked_at >= cutoff,
            SpaceResource.is_hidden.is_(False),
            Resource.is_removed.is_(False),
        )
        .count()
    )
    pending_appeals_count = SpaceModerationAppeal.query.filter_by(
        space_id=space.id,
        status="pending",
    ).count()
    pending_invitations = (
        SpaceInvitation.query.filter_by(space_id=space.id, status="pending")
        .order_by(SpaceInvitation.created_at.asc(), SpaceInvitation.id.asc())
        .all()
    )
    pending_invitations_count = len(pending_invitations)
    moderation_actions_30d = (
        SpaceModerationAction.query.filter(
            SpaceModerationAction.space_id == space.id,
            SpaceModerationAction.created_at >= cutoff,
        ).count()
    )
    recent_members = (
        SpaceMembership.query.filter_by(space_id=space.id)
        .order_by(SpaceMembership.joined_at.desc(), SpaceMembership.id.desc())
        .limit(10)
        .all()
    )
    membership_history = []
    if membership.role == "owner":
        membership_history = (
            SpaceMembershipAction.query.filter_by(space_id=space.id)
            .order_by(SpaceMembershipAction.created_at.desc(), SpaceMembershipAction.id.desc())
            .limit(50)
            .all()
        )

    metrics = {
        "member_count": member_count,
        "moderator_count": moderator_count,
        "new_members_30d": new_members_30d,
        "posts_30d": posts_30d,
        "resources_30d": resources_30d,
        "pending_appeals": pending_appeals_count,
        "pending_invitations": pending_invitations_count,
        "moderation_actions_30d": moderation_actions_30d,
    }
    return render_template(
        "spaces/operator_dashboard.html",
        space=space,
        membership=membership,
        metrics=metrics,
        recent_members=recent_members,
        membership_history=membership_history,
        pending_invitations=pending_invitations,
    )



@spaces_blueprint.get("/invitations")
@login_required
def invitations():
    pending = (
        SpaceInvitation.query.filter_by(
            invited_user_id=current_user.id,
            status="pending",
        )
        .order_by(SpaceInvitation.created_at.desc(), SpaceInvitation.id.desc())
        .all()
    )
    return render_template("spaces/invitations.html", invitations=pending)


@spaces_blueprint.post("/<slug>/invitations")
@login_required
def create_invitation(slug):
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    if not _can_moderate(membership):
        abort(403)

    username = (request.form.get("username") or "").strip()
    if not username:
        abort(400, description="Enter a Ripple username to invite.")

    invited_user = User.query.filter(
        db.func.lower(User.username) == username.casefold()
    ).first()
    if invited_user is None:
        abort(404, description="No Ripple user matches that username.")
    if SpaceMembership.query.filter_by(
        space_id=space.id,
        user_id=invited_user.id,
    ).first() is not None:
        abort(400, description="That user is already a member of this space.")

    existing = SpaceInvitation.query.filter_by(
        space_id=space.id,
        invited_user_id=invited_user.id,
        status="pending",
    ).first()
    if existing is not None:
        flash(f"@{invited_user.username} already has a pending invitation.", "info")
        return redirect(url_for("spaces.detail", slug=space.slug))

    db.session.add(
        SpaceInvitation(
            space_id=space.id,
            invited_user_id=invited_user.id,
            invited_by_id=current_user.id,
        )
    )
    db.session.add(
        Notification(
            user_id=invited_user.id,
            message=f"You were invited to join the {space.name} space.",
        )
    )
    db.session.commit()
    flash(f"Invitation sent to @{invited_user.username}.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))



@spaces_blueprint.post("/<slug>/invitations/<int:invitation_id>/cancel")
@login_required
def cancel_invitation(slug, invitation_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    if not _can_moderate(_membership(space)):
        abort(403)
    invitation = SpaceInvitation.query.filter_by(
        id=invitation_id,
        space_id=space.id,
    ).first_or_404()
    if invitation.status != "pending":
        abort(400, description="That invitation is no longer pending.")

    invitation.status = "canceled"
    invitation.responded_at = _utcnow()
    db.session.add(
        Notification(
            user_id=invitation.invited_user_id,
            message=f"Your invitation to the {space.name} space was canceled.",
        )
    )
    db.session.commit()
    flash(f"Invitation to @{invitation.invited_user.username} canceled.", "success")
    return redirect(url_for("spaces.operator_dashboard", slug=space.slug))


def _respond_to_invitation(invitation_id, *, decision):
    invitation = SpaceInvitation.query.filter_by(
        id=invitation_id,
        invited_user_id=current_user.id,
    ).first_or_404()
    if invitation.status != "pending":
        abort(400, description="That invitation is no longer pending.")

    invitation.status = decision
    invitation.responded_at = _utcnow()
    if decision == "accepted":
        membership = SpaceMembership.query.filter_by(
            space_id=invitation.space_id,
            user_id=current_user.id,
        ).first()
        if membership is None:
            db.session.add(
                SpaceMembership(
                    space_id=invitation.space_id,
                    user_id=current_user.id,
                    role="member",
                )
            )
    db.session.commit()
    flash(
        f"You joined {invitation.space.name}."
        if decision == "accepted"
        else f"You declined the invitation to {invitation.space.name}.",
        "success" if decision == "accepted" else "info",
    )
    return redirect(url_for("spaces.invitations"))


@spaces_blueprint.post("/invitations/<int:invitation_id>/accept")
@login_required
def accept_invitation(invitation_id):
    return _respond_to_invitation(invitation_id, decision="accepted")


@spaces_blueprint.post("/invitations/<int:invitation_id>/decline")
@login_required
def decline_invitation(invitation_id):
    return _respond_to_invitation(invitation_id, decision="declined")


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


@spaces_blueprint.post("/<slug>/ownership")
@login_required
def transfer_ownership(slug):
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    if membership is None or membership.role != "owner" or space.owner_id != current_user.id:
        abort(403)

    target_user_id = request.form.get("user_id", type=int)
    if target_user_id is None or request.form.get("confirm") != "transfer":
        abort(400, description="Choose a member and confirm the ownership transfer.")

    target = SpaceMembership.query.filter_by(
        space_id=space.id,
        user_id=target_user_id,
    ).first_or_404()
    if target.user_id == current_user.id or target.role == "owner":
        abort(400, description="Choose another current member as the new owner.")

    previous_owner = membership
    target_previous_role = target.role
    previous_owner.role = "member"
    target.role = "owner"
    space.owner_id = target.user_id
    _audit_membership(
        space,
        action_type="ownership_transferred",
        affected_user_id=target.user_id,
        previous_role=target_previous_role,
        new_role="owner",
        details=f"Ownership transferred from @{current_user.username}; previous owner became a member.",
    )
    db.session.add(
        Notification(
            user_id=target.user_id,
            message=f"You are now the owner of the {space.name} space.",
        )
    )
    db.session.commit()
    flash(
        f"Ownership transferred to @{target.user.username}. You remain a member and may now leave the space.",
        "success",
    )
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/members/<int:user_id>/remove")
@login_required
def remove_member(slug, user_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    if membership is None or membership.role != "owner" or space.owner_id != current_user.id:
        abort(403)

    target = SpaceMembership.query.filter_by(space_id=space.id, user_id=user_id).first_or_404()
    if target.role == "owner" or target.user_id == space.owner_id:
        abort(400, description="Transfer ownership before removing the current owner.")
    if request.form.get("confirm") != "remove":
        abort(400, description="Confirm the member removal.")

    removed_user = target.user
    removed_role = target.role
    _audit_membership(
        space,
        action_type="member_removed",
        affected_user_id=removed_user.id,
        previous_role=removed_role,
        new_role=None,
        details="Current Space membership ended by the owner; public rejoin remains available.",
    )
    db.session.delete(target)
    db.session.add(
        Notification(
            user_id=removed_user.id,
            message=f"Your membership in the {space.name} space was ended by the owner.",
        )
    )
    db.session.commit()
    flash(
        f"@{removed_user.username} was removed from {space.name}. Because this is a public space, they may join again.",
        "success",
    )
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
        _audit_membership(
            space,
            action_type="role_changed",
            affected_user_id=target.user_id,
            previous_role=old_role,
            new_role=role,
            details=f"Owner changed Space role from {old_role} to {role}.",
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
    if space.visibility == "private" and existing is None:
        abort(403, description="Private spaces require an accepted invitation.")
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
