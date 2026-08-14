"""Notification inbox route."""

from flask import render_template
from flask_login import current_user, login_required

from twitclone.extensions import db
from twitclone.models import Notification
from twitclone.notifications import notifications_blueprint


@login_required
def notifications():
    unread_count = Notification.query.filter_by(
        user_id=current_user.id, read=False
    ).update({"read": True}, synchronize_session=False)
    if unread_count:
        db.session.commit()

    user_notifications = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.timestamp.desc())
        .all()
    )
    return render_template("notifications.html", notifications=user_notifications)


@notifications_blueprint.record_once
def register_notification_routes(state):
    """Register the route while retaining its existing endpoint name."""
    state.app.add_url_rule(
        "/notifications", endpoint="notifications", view_func=notifications
    )
