"""Public reply thread routes for Sprint 14."""

from datetime import UTC, datetime

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.conversation_intent import conversation_intent_metadata
from twitclone.extensions import db
from twitclone.models import Notification, Tweet
from twitclone.reply_models import Reply
from twitclone.replies import replies_blueprint
from twitclone.spaces.models import SpacePost
from twitclone.timeline.validation import validate_post_content

MAX_PRESENTATION_DEPTH = 3


def _root_tweet(tweet_id):
    tweet = db.get_or_404(Tweet, tweet_id)
    now = datetime.now(UTC).replace(tzinfo=None)
    if tweet.is_removed or (tweet.scheduled_at is not None and tweet.scheduled_at > now):
        abort(404)
    if SpacePost.query.filter_by(tweet_id=tweet.id).first() is not None:
        abort(404)
    return tweet


def _intent(tweet):
    record = getattr(tweet, "conversation_intent_record", None)
    return conversation_intent_metadata(record.intent if record else None)


def _visible_reply(tweet_id, reply_id):
    return Reply.query.filter_by(id=reply_id, tweet_id=tweet_id, is_removed=False).first_or_404()


def _thread_rows(tweet_id):
    replies = Reply.query.filter_by(tweet_id=tweet_id, is_removed=False).order_by(Reply.created_at.asc(), Reply.id.asc()).all()
    by_parent = {}
    by_id = {reply.id: reply for reply in replies}
    for reply in replies:
        parent_id = reply.parent_reply_id if reply.parent_reply_id in by_id else None
        by_parent.setdefault(parent_id, []).append(reply)

    rows = []
    visited = set()

    def visit(reply, depth):
        if reply.id in visited:
            return
        visited.add(reply.id)
        rows.append({"reply": reply, "depth": min(depth, MAX_PRESENTATION_DEPTH), "actual_depth": depth})
        for child in by_parent.get(reply.id, []):
            visit(child, depth + 1)

    for root_reply in by_parent.get(None, []):
        visit(root_reply, 0)
    for reply in replies:
        visit(reply, 0)
    return rows


def _conversation_open(tweet):
    state = getattr(tweet, "conversation_state_record", None)
    return not (state and state.is_closed)


def _create_reply(tweet, *, parent=None):
    if not _conversation_open(tweet):
        abort(409)
    content = request.form.get("content")
    validation_error = validate_post_content(content, post_type="Reply")
    if validation_error:
        flash(validation_error, "danger")
        return redirect(url_for("timeline.thread", tweet_id=tweet.id))

    reply = Reply(
        tweet_id=tweet.id,
        user_id=current_user.id,
        parent_reply_id=parent.id if parent else None,
        content=content,
    )
    db.session.add(reply)
    db.session.flush()

    notification_user_id = parent.user_id if parent and parent.user_id != current_user.id else tweet.user_id
    if notification_user_id != current_user.id:
        db.session.add(Notification(
            user_id=notification_user_id,
            message=(
                f"{current_user.username} replied to your reply"
                if parent and notification_user_id == parent.user_id
                else f"{current_user.username} replied to your post"
            ),
            tweet_id=tweet.id,
        ))
    db.session.commit()
    flash("Your reply has been posted.", "success")
    return redirect(url_for("timeline.reply_permalink", tweet_id=tweet.id, reply_id=reply.id))


@replies_blueprint.route("/post/<int:tweet_id>/thread", methods=["GET"])
def thread(tweet_id):
    tweet = _root_tweet(tweet_id)
    return render_template(
        "replies/thread.html",
        tweet=tweet,
        reply_rows=_thread_rows(tweet.id),
        conversation_intent=_intent(tweet),
        max_presentation_depth=MAX_PRESENTATION_DEPTH,
    )


@replies_blueprint.route("/post/<int:tweet_id>/replies", methods=["POST"])
@login_required
def create_reply(tweet_id):
    tweet = _root_tweet(tweet_id)
    return _create_reply(tweet)


@replies_blueprint.route("/post/<int:tweet_id>/reply/<int:parent_reply_id>/replies", methods=["POST"])
@login_required
def create_nested_reply(tweet_id, parent_reply_id):
    tweet = _root_tweet(tweet_id)
    parent = _visible_reply(tweet.id, parent_reply_id)
    return _create_reply(tweet, parent=parent)


@replies_blueprint.route("/post/<int:tweet_id>/reply/<int:reply_id>", methods=["GET"])
def reply_permalink(tweet_id, reply_id):
    tweet = _root_tweet(tweet_id)
    reply = _visible_reply(tweet.id, reply_id)
    return redirect(url_for("timeline.thread", tweet_id=tweet.id, _anchor=f"reply-{reply.id}"))
