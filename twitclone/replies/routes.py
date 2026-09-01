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


@replies_blueprint.route("/post/<int:tweet_id>/thread", methods=["GET"])
def thread(tweet_id):
    tweet = _root_tweet(tweet_id)
    replies = Reply.query.filter_by(tweet_id=tweet.id, is_removed=False).order_by(Reply.created_at.asc(), Reply.id.asc()).all()
    return render_template("replies/thread.html", tweet=tweet, replies=replies, conversation_intent=_intent(tweet))


@replies_blueprint.route("/post/<int:tweet_id>/replies", methods=["POST"])
@login_required
def create_reply(tweet_id):
    tweet = _root_tweet(tweet_id)
    state = getattr(tweet, "conversation_state_record", None)
    if state and state.is_closed:
        abort(409)

    content = request.form.get("content")
    validation_error = validate_post_content(content, post_type="Reply")
    if validation_error:
        flash(validation_error, "danger")
        return redirect(url_for("replies.thread", tweet_id=tweet.id))

    reply = Reply(tweet_id=tweet.id, user_id=current_user.id, content=content)
    db.session.add(reply)
    db.session.flush()
    if tweet.user_id != current_user.id:
        db.session.add(Notification(user_id=tweet.user_id, message=f"{current_user.username} replied to your post", tweet_id=tweet.id))
    db.session.commit()
    flash("Your reply has been posted.", "success")
    return redirect(url_for("replies.reply_permalink", tweet_id=tweet.id, reply_id=reply.id))


@replies_blueprint.route("/post/<int:tweet_id>/reply/<int:reply_id>", methods=["GET"])
def reply_permalink(tweet_id, reply_id):
    tweet = _root_tweet(tweet_id)
    reply = Reply.query.filter_by(id=reply_id, tweet_id=tweet.id, is_removed=False).first_or_404()
    return redirect(url_for("replies.thread", tweet_id=tweet.id, _anchor=f"reply-{reply.id}"))
