"""Direct-message inbox and reply routes."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.extensions import db
from twitclone.messaging import messaging_blueprint
from twitclone.messaging.validation import validate_message_content
from twitclone.models import DirectMessage, Notification


@login_required
def messages():
    received_messages = (
        DirectMessage.query.filter_by(receiver_id=current_user.id)
        .order_by(DirectMessage.timestamp.desc())
        .all()
    )
    return render_template("messages.html", messages=received_messages)


@login_required
def reply_message(message_id):
    message = DirectMessage.query.filter_by(
        id=message_id, receiver_id=current_user.id
    ).first_or_404()
    if request.method == "POST":
        content = request.form.get("content")
        validation_error = validate_message_content(content)
        if validation_error:
            flash(validation_error, "danger")
            return redirect(url_for("messages"))

        reply = DirectMessage(
            content=content,
            sender_id=current_user.id,
            receiver_id=message.sender_id,
        )
        notification = Notification(
            user_id=message.sender_id,
            message=f"{current_user.username} replied to your message",
        )
        db.session.add_all([reply, notification])
        db.session.commit()
        flash("Your reply has been sent!", "success")
        return redirect(url_for("messages"))

    return render_template("reply.html", message=message)


@messaging_blueprint.record_once
def register_messaging_routes(state):
    """Register routes while retaining existing endpoint names."""
    state.app.add_url_rule("/messages", endpoint="messages", view_func=messages)
    state.app.add_url_rule(
        "/reply/<int:message_id>",
        endpoint="reply_message",
        view_func=reply_message,
        methods=["GET", "POST"],
    )
