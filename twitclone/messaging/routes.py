"""Direct-message inbox and reply routes."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.extensions import db
from twitclone.messaging import messaging_blueprint
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
    message = DirectMessage.query.get_or_404(message_id)
    if request.method == "POST":
        content = request.form["content"]
        if len(content) <= 500:
            reply = DirectMessage(
                content=content,
                sender_id=current_user.id,
                receiver_id=message.sender_id,
            )
            db.session.add(reply)
            db.session.commit()
            notification = Notification(
                user_id=message.sender_id,
                message=f"{current_user.username} replied to your message",
            )
            db.session.add(notification)
            db.session.commit()
            flash("Your reply has been sent!", "success")
        else:
            flash("Message content exceeds 500 characters.", "danger")
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
