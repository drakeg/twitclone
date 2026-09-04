"""Public reply thread routes for Sprint 14."""

from datetime import UTC, datetime

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.community.routes import REPORT_CATEGORIES
from twitclone.conversation_intent import conversation_intent_metadata
from twitclone.extensions import db
from twitclone.models import Notification, Tweet
from twitclone.reply_models import Reply, ReplyContribution, ReplyReport
from twitclone.replies import replies_blueprint
from twitclone.spaces.models import SpacePost
from twitclone.timeline.validation import validate_post_content

MAX_PRESENTATION_DEPTH = 3
MAX_REPLY_DEPTH = 12
CONTRIBUTION_SIGNALS = {"helpful": "Helpful", "thoughtful": "Thoughtful", "context": "Useful context"}


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


def _persisted_depth(reply, by_id):
    """Return persisted nesting depth without trusting a potentially cyclic parent chain."""
    depth = 0
    cursor = reply
    seen = {reply.id}
    while cursor.parent_reply_id is not None:
        parent = by_id.get(cursor.parent_reply_id)
        if parent is None or parent.id in seen:
            break
        seen.add(parent.id)
        depth += 1
        cursor = parent
    return depth


def _reply_depth(reply):
    """Return persisted depth for write-time enforcement."""
    depth = 0
    cursor = reply
    seen = {reply.id}
    while cursor.parent_reply_id is not None:
        parent = db.session.get(Reply, cursor.parent_reply_id)
        if parent is None or parent.tweet_id != reply.tweet_id or parent.id in seen:
            break
        seen.add(parent.id)
        depth += 1
        cursor = parent
    return depth


def _thread_rows(tweet_id):
    """Build the visible thread with bounded queries and removal-safe parent context."""
    all_replies = Reply.query.filter_by(tweet_id=tweet_id).order_by(Reply.created_at.asc(), Reply.id.asc()).all()
    by_id = {reply.id: reply for reply in all_replies}
    replies = [reply for reply in all_replies if not reply.is_removed]
    visible_ids = {reply.id for reply in replies}

    contributions_by_reply = {reply.id: [] for reply in replies}
    if visible_ids:
        contributions = ReplyContribution.query.filter(ReplyContribution.reply_id.in_(visible_ids)).all()
        for contribution in contributions:
            contributions_by_reply.setdefault(contribution.reply_id, []).append(contribution)

    by_parent = {}
    for reply in replies:
        parent_id = reply.parent_reply_id if reply.parent_reply_id in visible_ids else None
        by_parent.setdefault(parent_id, []).append(reply)

    rows = []
    visited = set()

    def visit(reply):
        if reply.id in visited:
            return
        visited.add(reply.id)
        contributions = contributions_by_reply.get(reply.id, [])
        signals = {
            key: {
                "label": label,
                "count": sum(item.signal == key for item in contributions),
                "selected": current_user.is_authenticated and any(
                    item.signal == key and item.user_id == current_user.id for item in contributions
                ),
            }
            for key, label in CONTRIBUTION_SIGNALS.items()
        }
        actual_depth = _persisted_depth(reply, by_id)
        parent = by_id.get(reply.parent_reply_id)
        rows.append({
            "reply": reply,
            "parent": parent if parent and not parent.is_removed else None,
            "parent_removed": bool(parent and parent.is_removed),
            "depth": min(actual_depth, MAX_PRESENTATION_DEPTH),
            "actual_depth": actual_depth,
            "can_reply": actual_depth < MAX_REPLY_DEPTH,
            "contribution_signals": signals,
        })
        for child in by_parent.get(reply.id, []):
            visit(child)

    for root_reply in by_parent.get(None, []):
        visit(root_reply)
    for reply in replies:
        visit(reply)
    return rows


def _conversation_open(tweet):
    state = getattr(tweet, "conversation_state_record", None)
    return not (state and state.is_closed)


def _create_reply(tweet, *, parent=None):
    if not _conversation_open(tweet):
        abort(409)
    if parent is not None and _reply_depth(parent) >= MAX_REPLY_DEPTH:
        flash("This reply thread has reached its maximum nesting depth.", "warning")
        return redirect(url_for("timeline.reply_permalink", tweet_id=tweet.id, reply_id=parent.id))

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
        max_reply_depth=MAX_REPLY_DEPTH,
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


@replies_blueprint.route("/post/<int:tweet_id>/reply/<int:reply_id>/contribution/<signal>", methods=["POST"])
@login_required
def toggle_reply_contribution(tweet_id, reply_id, signal):
    _root_tweet(tweet_id)
    reply = _visible_reply(tweet_id, reply_id)
    if signal not in CONTRIBUTION_SIGNALS:
        abort(404)
    if reply.user_id == current_user.id:
        flash("Constructive contribution signals are for recognizing someone else's reply.", "warning")
        return redirect(url_for("timeline.reply_permalink", tweet_id=tweet_id, reply_id=reply.id))

    existing = ReplyContribution.query.filter_by(
        user_id=current_user.id,
        reply_id=reply.id,
        signal=signal,
    ).first()
    if existing:
        db.session.delete(existing)
        flash(f"{CONTRIBUTION_SIGNALS[signal]} removed.", "success")
    else:
        db.session.add(ReplyContribution(user_id=current_user.id, reply_id=reply.id, signal=signal))
        flash(f"Marked {CONTRIBUTION_SIGNALS[signal].lower()}.", "success")
    db.session.commit()
    return redirect(url_for("timeline.reply_permalink", tweet_id=tweet_id, reply_id=reply.id))


@replies_blueprint.route("/post/<int:tweet_id>/reply/<int:reply_id>/report", methods=["GET", "POST"])
@login_required
def report_reply(tweet_id, reply_id):
    _root_tweet(tweet_id)
    reply = _visible_reply(tweet_id, reply_id)
    if reply.user_id == current_user.id:
        flash("You cannot report your own content.", "warning")
        return redirect(url_for("timeline.reply_permalink", tweet_id=tweet_id, reply_id=reply.id))

    existing = ReplyReport.query.filter_by(reporter_id=current_user.id, reply_id=reply.id).first()
    if existing:
        flash("You have already reported this content. An admin can review it.", "info")
        return redirect(url_for("timeline.reply_permalink", tweet_id=tweet_id, reply_id=reply.id))

    if request.method == "POST":
        category = request.form.get("category") or ""
        details = (request.form.get("details") or "").strip() or None
        if category not in REPORT_CATEGORIES:
            flash("Choose a reason for the report.", "danger")
        else:
            db.session.add(ReplyReport(
                reporter_id=current_user.id,
                author_id=reply.user_id,
                reply_id=reply.id,
                category=category,
                details=details,
            ))
            db.session.add(Notification(
                user_id=current_user.id,
                message="Your report was received and is awaiting Ripple admin review.",
            ))
            db.session.commit()
            flash("Report submitted. Ripple admins have been alerted for review.", "success")
            return redirect(url_for("timeline.reply_permalink", tweet_id=tweet_id, reply_id=reply.id))

    return render_template(
        "report_content.html",
        content=reply,
        content_type="reply",
        preview=reply.content,
        categories=REPORT_CATEGORIES,
    )


@replies_blueprint.route("/post/<int:tweet_id>/reply/<int:reply_id>", methods=["GET"])
def reply_permalink(tweet_id, reply_id):
    tweet = _root_tweet(tweet_id)
    reply = _visible_reply(tweet.id, reply_id)
    return redirect(url_for("timeline.thread", tweet_id=tweet.id, _anchor=f"reply-{reply.id}"))
