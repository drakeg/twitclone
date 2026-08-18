"""Notification inbox and deletion routes."""

from flask import abort, flash, redirect, render_template, url_for
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


@login_required
def delete_notification(notification_id):
    notification = db.session.get(Notification, notification_id)
    if notification is None or notification.user_id != current_user.id:
        abort(404)

    db.session.delete(notification)
    db.session.commit()
    flash("Notification deleted.", "success")
    return redirect(url_for("notifications"))


@notifications_blueprint.record_once
def register_notification_routes(state):
    """Register routes while retaining existing endpoint names."""
    state.app.add_url_rule(
        "/notifications", endpoint="notifications", view_func=notifications
    )
    state.app.add_url_rule(
        "/notifications/<int:notification_id>/delete",
        endpoint="delete_notification",
        view_func=delete_notification,
        methods=["POST"],
    )
