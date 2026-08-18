"""Direct-message inbox, compose, and reply routes."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.extensions import db
from twitclone.messaging import messaging_blueprint
from twitclone.messaging.validation import validate_message_content
from twitclone.models import DirectMessage, Notification, User


@login_required
def messages():
    unread_messages = DirectMessage.query.filter_by(
        receiver_id=current_user.id, read=False
    )
    if unread_messages.update({"read": True}, synchronize_session=False):
        db.session.commit()

    received_messages = (
        DirectMessage.query.filter_by(receiver_id=current_user.id)
        .order_by(DirectMessage.timestamp.desc())
        .all()
    )
    sent_messages = (
        DirectMessage.query.filter_by(sender_id=current_user.id)
        .order_by(DirectMessage.timestamp.desc())
        .all()
    )
    return render_template(
        "messages.html",
        messages=received_messages,
        sent_messages=sent_messages,
    )


@login_required
def new_message():
    recipient_username = (request.form.get("recipient") or request.args.get("to") or "").strip()

    if request.method == "POST":
        content = request.form.get("content")
        validation_error = validate_message_content(content)
        if not recipient_username:
            flash("Recipient username is required.", "danger")
        elif validation_error:
            flash(validation_error, "danger")
        else:
            recipient = User.query.filter_by(username=recipient_username).first()
            if recipient is None:
                flash("That Ripple user could not be found.", "danger")
            elif recipient.id == current_user.id:
                flash("You cannot send a direct message to yourself.", "danger")
            else:
                message = DirectMessage(
                    content=content.strip(),
                    sender_id=current_user.id,
                    receiver_id=recipient.id,
                )
                notification = Notification(
                    user_id=recipient.id,
                    message=f"{current_user.username} sent you a message",
                )
                db.session.add_all([message, notification])
                db.session.commit()
                flash(f"Your message to {recipient.username} has been sent.", "success")
                return redirect(url_for("messages"))

    return render_template("new_message.html", recipient_username=recipient_username)


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
            content=content.strip(),
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
        "/messages/new",
        endpoint="new_message",
        view_func=new_message,
        methods=["GET", "POST"],
    )
    state.app.add_url_rule(
        "/reply/<int:message_id>",
        endpoint="reply_message",
        view_func=reply_message,
        methods=["GET", "POST"],
    )
