"""Routes for persistent community/topic spaces."""

import csv
import io
import re
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import Response, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.extensions import db
from twitclone.models import Notification, Tweet, User
from twitclone.resource_models import Resource
from twitclone.spaces import spaces_blueprint
from twitclone.spaces.models import (
    Space,
    SpaceAnnouncement,
    SpaceAnnouncementAction,
    SpaceAnnouncementRead,
    SpaceCurationAction,
    SpaceEvent,
    SpaceEventAction,
    SpaceInvitation,
    SpaceLifecycleAction,
    SpaceMembership,
    SpaceMembershipAction,
    SpaceMembershipRequest,
    SpaceModerationAction,
    SpaceModerationAppeal,
    SpacePost,
    SpaceResource,
)
from twitclone.timeline.validation import validate_post_content

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_MEMBER_EXPORT_MAX_ROWS = 5000


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


def _slugify(value):
    slug = _SLUG_RE.sub("-", (value or "").strip().casefold()).strip("-")
    return slug[:80]


def _parse_event_start(local_value, timezone_name):
    try:
        local_start = datetime.fromisoformat(local_value)
    except (TypeError, ValueError):
        abort(400, description="Choose a valid event date and time.")

    if local_start.tzinfo is not None:
        abort(400, description="Enter event time without an embedded timezone offset.")

    try:
        timezone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        abort(400, description="Choose a valid IANA timezone such as America/New_York.")

    utc_candidates = set()
    for fold in (0, 1):
        candidate = local_start.replace(tzinfo=timezone, fold=fold)
        utc_value = candidate.astimezone(UTC)
        round_trip = utc_value.astimezone(timezone).replace(tzinfo=None)
        if round_trip == local_start:
            utc_candidates.add(utc_value.replace(tzinfo=None))

    if len(utc_candidates) != 1:
        abort(
            400,
            description=(
                "That local event time is ambiguous or does not exist because of "
                "a daylight-saving transition. Choose another time."
            ),
        )

    return utc_candidates.pop()


def _event_display_start(event):
    timezone = ZoneInfo(event.timezone)
    return (
        event.starts_at.replace(tzinfo=UTC)
        .astimezone(timezone)
        .strftime("%Y-%m-%d %H:%M")
    )


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


def _require_space_active(space):
    if space.archived_at is not None:
        abort(409, description="This space is archived and no longer accepts new participation.")


def _visible_space_posts(space):
    return (
        SpacePost.query.join(SpacePost.tweet)
        .filter(
            SpacePost.space_id == space.id,
            SpacePost.is_hidden.is_(False),
            Tweet.is_removed.is_(False),
        )
        .order_by(
            SpacePost.pinned_at.is_(None).asc(),
            SpacePost.pinned_at.desc(),
            Tweet.timestamp.desc(),
            SpacePost.id.desc(),
        )
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


def _audit_lifecycle(
    space,
    *,
    action_type,
    previous_name=None,
    new_name=None,
    previous_visibility=None,
    new_visibility=None,
    details=None,
):
    action = SpaceLifecycleAction(
        space_id=space.id,
        actor_id=current_user.id,
        action_type=action_type,
        previous_name=previous_name,
        new_name=new_name,
        previous_visibility=previous_visibility,
        new_visibility=new_visibility,
        details=details,
    )
    db.session.add(action)
    return action


def _audit_event(
    space,
    event,
    *,
    action_type,
    previous_title=None,
    new_title=None,
    previous_description=None,
    new_description=None,
    previous_location=None,
    new_location=None,
    previous_starts_at=None,
    new_starts_at=None,
    previous_timezone=None,
    new_timezone=None,
):
    action = SpaceEventAction(
        space_id=space.id,
        event_id=event.id,
        actor_id=current_user.id,
        action_type=action_type,
        previous_title=previous_title,
        new_title=new_title,
        previous_description=previous_description,
        new_description=new_description,
        previous_location=previous_location,
        new_location=new_location,
        previous_starts_at=previous_starts_at,
        new_starts_at=new_starts_at,
        previous_timezone=previous_timezone,
        new_timezone=new_timezone,
    )
    db.session.add(action)
    return action


def _audit_announcement(
    space,
    announcement,
    *,
    action_type,
    previous_title=None,
    new_title=None,
    previous_body=None,
    new_body=None,
):
    action = SpaceAnnouncementAction(
        space_id=space.id,
        announcement_id=announcement.id,
        actor_id=current_user.id,
        action_type=action_type,
        previous_title=previous_title,
        new_title=new_title,
        previous_body=previous_body,
        new_body=new_body,
    )
    db.session.add(action)
    return action


def _audit_curation(space, row, *, action_type, details=None):
    action = SpaceCurationAction(
        space_id=space.id,
        space_post_id=row.id,
        actor_id=current_user.id,
        action_type=action_type,
        details=details,
    )
    db.session.add(action)
    return action


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


def _member_admin_redirect(space):
    if request.form.get("return_to") != "roster":
        return redirect(url_for("spaces.detail", slug=space.slug))

    search = (request.form.get("roster_q") or "").strip()
    role = (request.form.get("roster_role") or "").strip().lower()
    if role not in {"", "owner", "moderator", "member"}:
        role = ""
    page = request.form.get("roster_page", type=int) or 1
    return redirect(
        url_for(
            "spaces.member_roster",
            slug=space.slug,
            q=search or None,
            role=role or None,
            page=max(page, 1),
        )
    )


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
    space_events = []
    event_history = []
    if membership is not None:
        event_query = SpaceEvent.query.filter(
            SpaceEvent.space_id == space.id,
            SpaceEvent.starts_at >= _utcnow(),
        )
        if not _can_moderate(membership):
            event_query = event_query.filter(SpaceEvent.is_canceled.is_(False))
        upcoming_events = (
            event_query.order_by(SpaceEvent.starts_at.asc(), SpaceEvent.id.asc())
            .limit(20)
            .all()
        )
        space_events = [
            {
                "event": event,
                "display_start": _event_display_start(event),
            }
            for event in upcoming_events
        ]
        if _can_moderate(membership):
            event_history = (
                SpaceEventAction.query.filter_by(space_id=space.id)
                .order_by(
                    SpaceEventAction.created_at.desc(),
                    SpaceEventAction.id.desc(),
                )
                .limit(50)
                .all()
            )

    space_announcements = []
    announcement_history = []
    if membership is not None:
        announcement_query = SpaceAnnouncement.query.filter_by(space_id=space.id)
        if not _can_moderate(membership):
            announcement_query = announcement_query.filter(
                SpaceAnnouncement.is_withdrawn.is_(False)
            )
        space_announcements = (
            announcement_query.order_by(
                SpaceAnnouncement.created_at.desc(),
                SpaceAnnouncement.id.desc(),
            )
            .limit(20)
            .all()
        )
        if _can_moderate(membership):
            announcement_history = (
                SpaceAnnouncementAction.query.filter_by(space_id=space.id)
                .order_by(
                    SpaceAnnouncementAction.created_at.desc(),
                    SpaceAnnouncementAction.id.desc(),
                )
                .limit(50)
                .all()
            )

    announcement_read_ids = set()
    unread_announcement_count = 0
    if membership is not None and space_announcements:
        visible_ids = [
            row.id
            for row in space_announcements
            if not row.is_withdrawn
        ]
        if visible_ids:
            announcement_read_ids = {
                row.announcement_id
                for row in SpaceAnnouncementRead.query.filter(
                    SpaceAnnouncementRead.user_id == current_user.id,
                    SpaceAnnouncementRead.announcement_id.in_(visible_ids),
                ).all()
            }
            unread_announcement_count = sum(
                1 for announcement_id in visible_ids
                if announcement_id not in announcement_read_ids
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
        space_events=space_events,
        event_history=event_history,
        space_announcements=space_announcements,
        announcement_history=announcement_history,
        announcement_read_ids=announcement_read_ids,
        unread_announcement_count=unread_announcement_count,
        space_posts=_visible_space_posts(space),
        space_resources=_visible_space_resources(space),
        resource_candidates=_resource_candidates(space) if membership else [],
        moderation_history=moderation_history,
        pending_appeals=pending_appeals,
        my_moderation=my_moderation,
        appeals_by_action=appeals_by_action,
        can_moderate=_can_moderate(membership),
    )





@spaces_blueprint.post("/<slug>/events")
@login_required
def create_event(slug):
    """Create a timezone-explicit upcoming event for Space members."""
    space = Space.query.filter_by(slug=slug).first_or_404()
    _require_space_active(space)
    if not _can_moderate(_membership(space)):
        abort(403)

    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    location = (request.form.get("location") or "").strip()
    timezone_name = (request.form.get("timezone") or "").strip()
    local_start = (request.form.get("starts_at") or "").strip()

    if not title or len(title) > 120:
        abort(400, description="Event title must be between 1 and 120 characters.")
    if not description or len(description) > 1000:
        abort(400, description="Event description must be between 1 and 1000 characters.")
    if len(location) > 200:
        abort(400, description="Event location must be 200 characters or fewer.")
    if not timezone_name or len(timezone_name) > 64:
        abort(400, description="Event timezone must be a valid IANA timezone.")

    starts_at = _parse_event_start(local_start, timezone_name)
    if starts_at <= _utcnow():
        abort(400, description="Event start time must be in the future.")

    event = SpaceEvent(
        space_id=space.id,
        created_by_id=current_user.id,
        title=title,
        description=description,
        location=location or None,
        starts_at=starts_at,
        timezone=timezone_name,
    )
    db.session.add(event)
    db.session.flush()
    _audit_event(
        space,
        event,
        action_type="created",
        new_title=title,
        new_description=description,
        new_location=location or None,
        new_starts_at=starts_at,
        new_timezone=timezone_name,
    )
    db.session.commit()
    flash("Space event scheduled.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/events/<int:event_id>/edit")
@login_required
def edit_event(slug, event_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    _require_space_active(space)
    if not _can_moderate(_membership(space)):
        abort(403)
    event = SpaceEvent.query.filter_by(id=event_id, space_id=space.id).first_or_404()
    if event.is_canceled:
        abort(409, description="Restore a canceled event before editing it.")

    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    location = (request.form.get("location") or "").strip()
    timezone_name = (request.form.get("timezone") or "").strip()
    local_start = (request.form.get("starts_at") or "").strip()

    if not title or len(title) > 120:
        abort(400, description="Event title must be between 1 and 120 characters.")
    if not description or len(description) > 1000:
        abort(400, description="Event description must be between 1 and 1000 characters.")
    if len(location) > 200:
        abort(400, description="Event location must be 200 characters or fewer.")
    if not timezone_name or len(timezone_name) > 64:
        abort(400, description="Event timezone must be a valid IANA timezone.")

    starts_at = _parse_event_start(local_start, timezone_name)
    if starts_at <= _utcnow():
        abort(400, description="Event start time must be in the future.")

    changed = (
        event.title != title
        or event.description != description
        or event.location != (location or None)
        or event.starts_at != starts_at
        or event.timezone != timezone_name
    )
    if changed:
        previous = {
            "title": event.title,
            "description": event.description,
            "location": event.location,
            "starts_at": event.starts_at,
            "timezone": event.timezone,
        }
        event.title = title
        event.description = description
        event.location = location or None
        event.starts_at = starts_at
        event.timezone = timezone_name
        event.updated_at = _utcnow()
        _audit_event(
            space,
            event,
            action_type="edited",
            previous_title=previous["title"],
            new_title=title,
            previous_description=previous["description"],
            new_description=description,
            previous_location=previous["location"],
            new_location=location or None,
            previous_starts_at=previous["starts_at"],
            new_starts_at=starts_at,
            previous_timezone=previous["timezone"],
            new_timezone=timezone_name,
        )
        db.session.commit()
        flash("Space event updated.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/events/<int:event_id>/cancel")
@login_required
def cancel_event(slug, event_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    _require_space_active(space)
    if not _can_moderate(_membership(space)):
        abort(403)
    event = SpaceEvent.query.filter_by(id=event_id, space_id=space.id).first_or_404()
    if not event.is_canceled:
        event.is_canceled = True
        event.canceled_at = _utcnow()
        event.canceled_by_id = current_user.id
        _audit_event(
            space,
            event,
            action_type="canceled",
            previous_title=event.title,
            new_title=event.title,
            previous_description=event.description,
            new_description=event.description,
            previous_location=event.location,
            new_location=event.location,
            previous_starts_at=event.starts_at,
            new_starts_at=event.starts_at,
            previous_timezone=event.timezone,
            new_timezone=event.timezone,
        )
        db.session.commit()
        flash("Space event canceled.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/events/<int:event_id>/restore")
@login_required
def restore_event(slug, event_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    _require_space_active(space)
    if not _can_moderate(_membership(space)):
        abort(403)
    event = SpaceEvent.query.filter_by(id=event_id, space_id=space.id).first_or_404()
    if event.is_canceled:
        if event.starts_at <= _utcnow():
            abort(409, description="Past events cannot be restored.")
        event.is_canceled = False
        event.canceled_at = None
        event.canceled_by_id = None
        _audit_event(
            space,
            event,
            action_type="restored",
            previous_title=event.title,
            new_title=event.title,
            previous_description=event.description,
            new_description=event.description,
            previous_location=event.location,
            new_location=event.location,
            previous_starts_at=event.starts_at,
            new_starts_at=event.starts_at,
            previous_timezone=event.timezone,
            new_timezone=event.timezone,
        )
        db.session.commit()
        flash("Space event restored.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/announcements")
@login_required
def create_announcement(slug):
    """Publish a durable member-only Space announcement."""
    space = Space.query.filter_by(slug=slug).first_or_404()
    _require_space_active(space)
    membership = _membership(space)
    if not _can_moderate(membership):
        abort(403)

    title = (request.form.get("title") or "").strip()
    body = (request.form.get("body") or "").strip()
    if not title or len(title) > 120:
        abort(400, description="Announcement title must be between 1 and 120 characters.")
    if not body or len(body) > 1000:
        abort(400, description="Announcement body must be between 1 and 1000 characters.")

    announcement = SpaceAnnouncement(
        space_id=space.id,
        author_id=current_user.id,
        title=title,
        body=body,
    )
    db.session.add(announcement)
    db.session.flush()
    _audit_announcement(
        space,
        announcement,
        action_type="created",
        new_title=title,
        new_body=body,
    )
    db.session.commit()
    flash("Space announcement published.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/announcements/<int:announcement_id>/edit")
@login_required
def edit_announcement(slug, announcement_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    _require_space_active(space)
    if not _can_moderate(_membership(space)):
        abort(403)
    announcement = SpaceAnnouncement.query.filter_by(
        id=announcement_id,
        space_id=space.id,
    ).first_or_404()
    if announcement.is_withdrawn:
        abort(409, description="Restore a withdrawn announcement before editing it.")

    title = (request.form.get("title") or "").strip()
    body = (request.form.get("body") or "").strip()
    if not title or len(title) > 120:
        abort(400, description="Announcement title must be between 1 and 120 characters.")
    if not body or len(body) > 1000:
        abort(400, description="Announcement body must be between 1 and 1000 characters.")

    if announcement.title != title or announcement.body != body:
        previous_title = announcement.title
        previous_body = announcement.body
        announcement.title = title
        announcement.body = body
        announcement.updated_at = _utcnow()
        _audit_announcement(
            space,
            announcement,
            action_type="edited",
            previous_title=previous_title,
            new_title=title,
            previous_body=previous_body,
            new_body=body,
        )
        db.session.commit()
        flash("Space announcement updated.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/announcements/<int:announcement_id>/withdraw")
@login_required
def withdraw_announcement(slug, announcement_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    _require_space_active(space)
    if not _can_moderate(_membership(space)):
        abort(403)
    announcement = SpaceAnnouncement.query.filter_by(
        id=announcement_id,
        space_id=space.id,
    ).first_or_404()
    if not announcement.is_withdrawn:
        announcement.is_withdrawn = True
        announcement.withdrawn_at = _utcnow()
        announcement.withdrawn_by_id = current_user.id
        _audit_announcement(
            space,
            announcement,
            action_type="withdrawn",
            previous_title=announcement.title,
            new_title=announcement.title,
            previous_body=announcement.body,
            new_body=announcement.body,
        )
        db.session.commit()
        flash("Space announcement withdrawn from members.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/announcements/<int:announcement_id>/restore")
@login_required
def restore_announcement(slug, announcement_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    _require_space_active(space)
    if not _can_moderate(_membership(space)):
        abort(403)
    announcement = SpaceAnnouncement.query.filter_by(
        id=announcement_id,
        space_id=space.id,
    ).first_or_404()
    if announcement.is_withdrawn:
        announcement.is_withdrawn = False
        announcement.withdrawn_at = None
        announcement.withdrawn_by_id = None
        _audit_announcement(
            space,
            announcement,
            action_type="restored",
            previous_title=announcement.title,
            new_title=announcement.title,
            previous_body=announcement.body,
            new_body=announcement.body,
        )
        db.session.commit()
        flash("Space announcement restored to members.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/announcements/<int:announcement_id>/read")
@login_required
def mark_announcement_read(slug, announcement_id):
    """Mark a currently visible Space announcement read for this member only."""
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    if membership is None:
        abort(403)

    announcement = SpaceAnnouncement.query.filter_by(
        id=announcement_id,
        space_id=space.id,
    ).first_or_404()
    if announcement.is_withdrawn:
        abort(404)

    existing = SpaceAnnouncementRead.query.filter_by(
        announcement_id=announcement.id,
        user_id=current_user.id,
    ).first()
    if existing is None:
        db.session.add(
            SpaceAnnouncementRead(
                announcement_id=announcement.id,
                user_id=current_user.id,
            )
        )
        db.session.commit()

    return redirect(
        url_for("spaces.detail", slug=space.slug) + "#space-announcements-heading"
    )


@spaces_blueprint.post("/<slug>/archive")
@login_required
def archive_space(slug):
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    if membership is None or membership.role != "owner" or space.owner_id != current_user.id:
        abort(403)
    if space.archived_at is not None:
        return redirect(url_for("spaces.detail", slug=space.slug))
    if request.form.get("confirm") != "archive":
        abort(400, description="Confirm the Space archive action.")

    space.archived_at = _utcnow()
    space.archived_by_id = current_user.id
    _audit_lifecycle(
        space,
        action_type="archived",
        previous_name=space.name,
        new_name=space.name,
        previous_visibility=space.visibility,
        new_visibility=space.visibility,
        details="Participation paused; existing Space data preserved.",
    )
    db.session.commit()
    flash(
        f"{space.name} was archived. Existing history remains available, but new participation is paused.",
        "success",
    )
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/restore")
@login_required
def restore_space(slug):
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    if membership is None or membership.role != "owner" or space.owner_id != current_user.id:
        abort(403)
    if space.archived_at is None:
        return redirect(url_for("spaces.detail", slug=space.slug))
    if request.form.get("confirm") != "restore":
        abort(400, description="Confirm the Space restore action.")

    space.archived_at = None
    space.archived_by_id = None
    _audit_lifecycle(
        space,
        action_type="restored",
        previous_name=space.name,
        new_name=space.name,
        previous_visibility=space.visibility,
        new_visibility=space.visibility,
        details="Participation resumed under the existing visibility settings.",
    )
    db.session.commit()
    flash(f"{space.name} was restored and is accepting participation again.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.route("/<slug>/settings", methods=["GET", "POST"])
@login_required
def settings(slug):
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    if membership is None or membership.role != "owner" or space.owner_id != current_user.id:
        abort(403)

    if request.method == "POST":
        _require_space_active(space)
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

        previous_name = space.name
        previous_description = space.description
        previous_visibility = space.visibility
        space.name = name
        space.description = description
        space.visibility = visibility
        _audit_lifecycle(
            space,
            action_type="settings_updated",
            previous_name=previous_name,
            new_name=name,
            previous_visibility=previous_visibility,
            new_visibility=visibility,
            details=(
                "description_updated"
                if previous_description != description
                else "description_unchanged"
            ),
        )
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
    pending_membership_requests = (
        SpaceMembershipRequest.query.filter_by(space_id=space.id, status="pending")
        .order_by(SpaceMembershipRequest.created_at.asc(), SpaceMembershipRequest.id.asc())
        .all()
    )
    pending_membership_requests_count = len(pending_membership_requests)
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
    lifecycle_history = []
    curation_history = (
        SpaceCurationAction.query.filter_by(space_id=space.id)
        .order_by(SpaceCurationAction.created_at.desc(), SpaceCurationAction.id.desc())
        .limit(50)
        .all()
    )
    if membership.role == "owner":
        membership_history = (
            SpaceMembershipAction.query.filter_by(space_id=space.id)
            .order_by(SpaceMembershipAction.created_at.desc(), SpaceMembershipAction.id.desc())
            .limit(50)
            .all()
        )
        lifecycle_history = (
            SpaceLifecycleAction.query.filter_by(space_id=space.id)
            .order_by(SpaceLifecycleAction.created_at.desc(), SpaceLifecycleAction.id.desc())
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
        "pending_membership_requests": pending_membership_requests_count,
        "moderation_actions_30d": moderation_actions_30d,
    }
    return render_template(
        "spaces/operator_dashboard.html",
        space=space,
        membership=membership,
        metrics=metrics,
        recent_members=recent_members,
        membership_history=membership_history,
        lifecycle_history=lifecycle_history,
        curation_history=curation_history,
        pending_invitations=pending_invitations,
        pending_membership_requests=pending_membership_requests,
        request_access_url=(
            url_for("spaces.request_access", slug=space.slug, _external=True)
            if space.visibility == "private"
            else None
        ),
    )



def _member_roster_filters():
    search = (request.args.get("q") or "").strip()
    role = (request.args.get("role") or "").strip().lower()
    if role not in {"", "owner", "moderator", "member"}:
        role = ""
    return search, role


def _member_roster_query(space, search, role):
    query = (
        SpaceMembership.query.join(SpaceMembership.user)
        .filter(SpaceMembership.space_id == space.id)
    )
    if search:
        query = query.filter(
            db.func.lower(User.username).like(f"%{search.casefold()}%")
        )
    if role:
        query = query.filter(SpaceMembership.role == role)
    return query


def _ordered_member_roster_query(query):
    return query.order_by(
        db.func.lower(User.username).asc(),
        SpaceMembership.id.asc(),
    )


def _spreadsheet_safe_csv_text(value):
    """Neutralize spreadsheet formula interpretation without changing stored data."""
    text = str(value)
    trimmed = text.lstrip()
    if text[:1] in {"\t", "\r", "\n"} or trimmed[:1] in {"=", "+", "-", "@"}:
        return f"'{text}"
    return text


def _utc_export_timestamp(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    else:
        value = value.astimezone(UTC)
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


@spaces_blueprint.get("/<slug>/members")
@login_required
def member_roster(slug):
    """Searchable operator-only Space membership roster."""
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    if not _can_moderate(membership):
        abort(403)

    search, role = _member_roster_filters()
    query = _member_roster_query(space, search, role)

    total_items = query.count()
    per_page = 25
    total_pages = max(1, (total_items + per_page - 1) // per_page)
    requested_page = request.args.get("page", default=1, type=int) or 1
    page = min(max(requested_page, 1), total_pages)
    rows = (
        _ordered_member_roster_query(query)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return render_template(
        "spaces/member_roster.html",
        space=space,
        membership=membership,
        rows=rows,
        search=search,
        selected_role=role,
        page=page,
        per_page=per_page,
        total_items=total_items,
        total_pages=total_pages,
        export_max_rows=_MEMBER_EXPORT_MAX_ROWS,
    )


@spaces_blueprint.get("/<slug>/members/export.csv")
@login_required
def export_member_roster(slug):
    """Export a bounded, filtered operator membership report."""
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    if not _can_moderate(membership):
        abort(403)

    search, role = _member_roster_filters()
    query = _ordered_member_roster_query(
        _member_roster_query(space, search, role)
    )
    rows = query.limit(_MEMBER_EXPORT_MAX_ROWS + 1).all()
    if len(rows) > _MEMBER_EXPORT_MAX_ROWS:
        abort(
            413,
            description=(
                f"Membership export is limited to {_MEMBER_EXPORT_MAX_ROWS} rows. "
                "Narrow the username or role filter and try again."
            ),
        )

    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["username", "space_role", "joined_at_utc"])
    for row in rows:
        writer.writerow(
            [
                _spreadsheet_safe_csv_text(row.user.username),
                row.role,
                _utc_export_timestamp(row.joined_at),
            ]
        )

    response = Response(output.getvalue(), content_type="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{space.slug}-members.csv"'
    )
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@spaces_blueprint.route("/<slug>/request-access", methods=["GET", "POST"])
@login_required
def request_access(slug):
    """Minimal private-Space membership request surface without content exposure."""
    space = Space.query.filter_by(slug=slug).first_or_404()
    if space.visibility != "private":
        return redirect(url_for("spaces.detail", slug=space.slug))
    if _membership(space) is not None:
        return redirect(url_for("spaces.detail", slug=space.slug))

    pending = SpaceMembershipRequest.query.filter_by(
        space_id=space.id,
        requester_id=current_user.id,
        status="pending",
    ).first()

    if request.method == "POST":
        _require_space_active(space)
        if pending is not None:
            flash("You already have a pending membership request for this Space.", "info")
            return redirect(url_for("spaces.request_access", slug=space.slug))

        pending_invitation = SpaceInvitation.query.filter_by(
            space_id=space.id,
            invited_user_id=current_user.id,
            status="pending",
        ).first()
        if pending_invitation is not None:
            flash(
                "You already have a pending invitation to this Space. Respond to that invitation instead.",
                "info",
            )
            return redirect(url_for("spaces.invitations"))

        note = (request.form.get("note") or "").strip()
        if len(note) > 500:
            abort(400, description="Membership request notes must be 500 characters or fewer.")

        membership_request = SpaceMembershipRequest(
            space_id=space.id,
            requester_id=current_user.id,
            note=note or None,
        )
        db.session.add(membership_request)
        operator_ids = {
            row.user_id
            for row in SpaceMembership.query.filter(
                SpaceMembership.space_id == space.id,
                SpaceMembership.role.in_(["owner", "moderator"]),
            ).all()
        }
        for operator_id in operator_ids:
            db.session.add(
                Notification(
                    user_id=operator_id,
                    message=f"@{current_user.username} requested access to the {space.name} space.",
                )
            )
        db.session.commit()
        flash("Membership request sent to the Space operators.", "success")
        return redirect(url_for("spaces.request_access", slug=space.slug))

    latest = (
        SpaceMembershipRequest.query.filter_by(
            space_id=space.id,
            requester_id=current_user.id,
        )
        .order_by(SpaceMembershipRequest.created_at.desc(), SpaceMembershipRequest.id.desc())
        .first()
    )
    return render_template(
        "spaces/request_access.html",
        space=space,
        pending_request=pending,
        latest_request=latest,
    )


def _resolve_membership_request(space, membership_request, *, decision):
    _require_space_active(space)
    if not _can_moderate(_membership(space)):
        abort(403)
    if membership_request.space_id != space.id:
        abort(404)
    if membership_request.status != "pending":
        abort(400, description="That membership request is no longer pending.")

    membership_request.status = decision
    membership_request.resolved_at = _utcnow()
    membership_request.resolved_by_id = current_user.id

    if decision == "approved":
        existing = SpaceMembership.query.filter_by(
            space_id=space.id,
            user_id=membership_request.requester_id,
        ).first()
        if existing is None:
            db.session.add(
                SpaceMembership(
                    space_id=space.id,
                    user_id=membership_request.requester_id,
                    role="member",
                )
            )
        pending_invitation = SpaceInvitation.query.filter_by(
            space_id=space.id,
            invited_user_id=membership_request.requester_id,
            status="pending",
        ).first()
        if pending_invitation is not None:
            pending_invitation.status = "canceled"
            pending_invitation.responded_at = _utcnow()

    db.session.add(
        Notification(
            user_id=membership_request.requester_id,
            message=(
                f"Your request to join the {space.name} space was approved."
                if decision == "approved"
                else f"Your request to join the {space.name} space was denied."
            ),
        )
    )
    db.session.commit()
    flash(
        (
            f"@{membership_request.requester.username} is now a member."
            if decision == "approved"
            else f"Membership request from @{membership_request.requester.username} denied."
        ),
        "success" if decision == "approved" else "info",
    )
    return redirect(url_for("spaces.operator_dashboard", slug=space.slug))


@spaces_blueprint.post("/<slug>/membership-requests/<int:request_id>/approve")
@login_required
def approve_membership_request(slug, request_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership_request = SpaceMembershipRequest.query.filter_by(id=request_id).first_or_404()
    return _resolve_membership_request(space, membership_request, decision="approved")


@spaces_blueprint.post("/<slug>/membership-requests/<int:request_id>/deny")
@login_required
def deny_membership_request(slug, request_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership_request = SpaceMembershipRequest.query.filter_by(id=request_id).first_or_404()
    return _resolve_membership_request(space, membership_request, decision="denied")


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
    _require_space_active(space)
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

    pending_request = SpaceMembershipRequest.query.filter_by(
        space_id=space.id,
        requester_id=invited_user.id,
        status="pending",
    ).first()
    if pending_request is not None:
        flash(
            f"@{invited_user.username} already requested membership. Review that request instead.",
            "info",
        )
        return redirect(url_for("spaces.operator_dashboard", slug=space.slug))

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

    if decision == "accepted":
        _require_space_active(invitation.space)

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
        pending_request = SpaceMembershipRequest.query.filter_by(
            space_id=invitation.space_id,
            requester_id=current_user.id,
            status="pending",
        ).first()
        if pending_request is not None:
            pending_request.status = "approved"
            pending_request.resolved_at = _utcnow()
            pending_request.resolved_by_id = invitation.invited_by_id
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
    _require_space_active(space)
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
    _require_space_active(space)
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
    return _member_admin_redirect(space)


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
    return _member_admin_redirect(space)


@spaces_blueprint.post("/<slug>/posts/<int:space_post_id>/pin")
@login_required
def pin_post(slug, space_post_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    _require_space_active(space)
    if not _can_moderate(_membership(space)):
        abort(403)
    row = SpacePost.query.filter_by(id=space_post_id, space_id=space.id).first_or_404()
    if row.is_hidden or row.tweet.is_removed:
        abort(409, description="Hidden or removed Space posts cannot be pinned.")
    if row.pinned_at is None:
        row.pinned_at = _utcnow()
        row.pinned_by_id = current_user.id
        _audit_curation(
            space,
            row,
            action_type="pin_post",
            details="Pinned for Space-local conversation curation.",
        )
        db.session.commit()
        flash("Conversation pinned in this Space.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/posts/<int:space_post_id>/unpin")
@login_required
def unpin_post(slug, space_post_id):
    space = Space.query.filter_by(slug=slug).first_or_404()
    _require_space_active(space)
    if not _can_moderate(_membership(space)):
        abort(403)
    row = SpacePost.query.filter_by(id=space_post_id, space_id=space.id).first_or_404()
    if row.pinned_at is not None:
        row.pinned_at = None
        row.pinned_by_id = None
        _audit_curation(
            space,
            row,
            action_type="unpin_post",
            details="Removed Space-local pin.",
        )
        db.session.commit()
        flash("Conversation unpinned.", "success")
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
    if row.pinned_at is not None:
        row.pinned_at = None
        row.pinned_by_id = None
        _audit_curation(
            space,
            row,
            action_type="unpin_post",
            details="Automatically unpinned when the Space post was hidden.",
        )
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
    _require_space_active(space)
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
