"""Timeline and post routes."""

from datetime import UTC, datetime, timedelta

from flask import abort, flash, redirect, render_template, request, send_file, url_for
from io import BytesIO
from flask_login import current_user, login_required
from twitclone.analytics_tracking import record_post_impression, record_post_impressions
from twitclone.contribution_models import ConstructiveContribution
from twitclone.conversation_intent import CONVERSATION_INTENTS, conversation_intent_metadata, normalize_conversation_intent
from twitclone.conversation_models import TweetConversationIntent
from twitclone.extensions import db
from twitclone.mentions import add_mention_notifications
from twitclone.media_storage import MediaNotFound, get_media_storage
from twitclone.models import DirectMessage, Notification, Quote, Retweet, Tweet, User
from twitclone.timeline import timeline_blueprint
from twitclone.timeline.media import store_image_upload
from twitclone.timeline.service import FEED_MODES, build_timeline_posts, paginate_timeline_posts
from twitclone.timeline.validation import validate_post_content
from twitclone.topic_models import associate_topics, public_topic_associations, replace_explicit_topics
from twitclone.utils import get_newest_users, get_trending_hashtags

CONTRIBUTION_SIGNALS = {"helpful": "Helpful", "thoughtful": "Thoughtful", "context": "Useful context"}


def _tweet_conversation_intent(tweet):
    stored_intent = tweet.conversation_intent_record.intent if tweet.conversation_intent_record else None
    return conversation_intent_metadata(stored_intent)


def _tweet_contribution_state(tweet):
    rows = ConstructiveContribution.query.filter_by(tweet_id=tweet.id).all()
    return {key: {"label": label, "count": sum(row.signal == key for row in rows), "selected": current_user.is_authenticated and any(row.signal == key and row.user_id == current_user.id for row in rows)} for key, label in CONTRIBUTION_SIGNALS.items()}


def index():
    now = datetime.now(UTC).replace(tzinfo=None)
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    requested_mode = (request.args.get("feed") or "all").strip().lower()
    feed_mode = requested_mode if requested_mode in FEED_MODES else "all"
    if feed_mode == "following" and not current_user.is_authenticated:
        feed_mode = "all"
    posts = build_timeline_posts(now=now, viewer=current_user, feed_mode=feed_mode)
    page = request.args.get("page", default=1, type=int) or 1
    timeline_page = paginate_timeline_posts(posts, page=page)
    record_post_impressions(timeline_page.items)
    return render_template("index.html", posts=timeline_page.items, timeline_page=timeline_page, current_time=current_time, trending_hashtags=get_trending_hashtags(), newest_users=get_newest_users(), conversation_intents=CONVERSATION_INTENTS, feed_mode=feed_mode)


def post_detail(tweet_id):
    tweet = db.get_or_404(Tweet, tweet_id); now = datetime.now(UTC).replace(tzinfo=None)
    if tweet.is_removed or (tweet.scheduled_at is not None and tweet.scheduled_at > now): abort(404)
    record_post_impression(tweet)
    return render_template("post_detail.html", tweet=tweet, conversation_intent=_tweet_conversation_intent(tweet), contribution_signals=_tweet_contribution_state(tweet), topic_associations=public_topic_associations(tweet))


def _scheduled_at_from_form():
    scheduled_date = request.form.get("scheduled_date"); scheduled_time = request.form.get("scheduled_time")
    if not scheduled_date and not scheduled_time: return None, None
    if not scheduled_date or not scheduled_time: return None, "Choose both a date and time to schedule a post."
    try: scheduled_at = datetime.strptime(f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M")
    except ValueError: return None, "Choose a valid schedule date and time."
    now = datetime.now(UTC).replace(tzinfo=None)
    if scheduled_at <= now: return None, "Scheduled posts must be set for a future time."
    max_days = 90 if current_user.has_entitlement('ripple_plus') else 7
    if scheduled_at > now + timedelta(days=max_days):
        if max_days == 7: return None, "Free accounts can schedule up to 7 days ahead. Ripple+ extends scheduling to 90 days."
        return None, "Ripple+ posts can be scheduled up to 90 days ahead."
    return scheduled_at, None


@login_required
def tweet():
    content = request.form.get("content"); validation_error = validate_post_content(content, post_type="Tweet")
    if validation_error: flash(validation_error, "danger"); return redirect(url_for("index"))
    image = request.files.get("image"); image_filename = None; original_image_filename = None
    if image and image.filename:
        image_error, original_image_filename, image_filename = store_image_upload(image, get_media_storage())
        if image_error: flash(image_error, "danger"); return redirect(url_for("index"))
    scheduled_at, schedule_error = _scheduled_at_from_form()
    if schedule_error: flash(schedule_error, "danger"); return redirect(url_for("index"))
    if content.startswith("/dm "):
        dm_parts = content.split(" ", 2)
        if len(dm_parts) == 3:
            username, message = dm_parts[1], dm_parts[2]; user = User.query.filter_by(username=username).first()
            if user: db.session.add_all([DirectMessage(content=message, sender_id=current_user.id, receiver_id=user.id), Notification(user_id=user.id, message=f"{current_user.username} sent you a message")]); db.session.commit(); flash("Your direct message has been sent!", "success")
            else: flash("User not found.", "danger")
    else:
        intent = normalize_conversation_intent(request.form.get("conversation_intent")); new_tweet = Tweet(content=content, user_id=current_user.id, image=image_filename, original_image=original_image_filename, scheduled_at=scheduled_at)
        db.session.add(new_tweet); db.session.flush(); db.session.add(TweetConversationIntent(tweet_id=new_tweet.id, intent=intent)); associate_topics(new_tweet, explicit_raw=request.form.get("topics"), content=content)
        if scheduled_at is None: add_mention_notifications(content=content, author=current_user, tweet_id=new_tweet.id)
        db.session.commit(); flash("Your tweet has been scheduled!" if scheduled_at else "Your tweet has been posted!", "success")
    return redirect(url_for("index"))


@login_required
def update_post_topics(tweet_id):
    tweet = db.get_or_404(Tweet, tweet_id)
    if tweet.is_removed: abort(404)
    if tweet.user_id != current_user.id: abort(403)
    replace_explicit_topics(tweet, request.form.get("topics")); db.session.commit(); flash("Post topics updated. Topic contribution history is recalculated from the current associations.", "success"); return redirect(url_for("post_detail", tweet_id=tweet.id))


def uploaded_file(filename):
    if not filename.startswith(("thumb_", "banner_")): abort(404)
    try: media = get_media_storage().get(filename)
    except (MediaNotFound, ValueError): abort(404)
    return send_file(BytesIO(media.content), mimetype=media.content_type, download_name=filename, max_age=31536000)


@login_required
def retweet(tweet_id):
    original_tweet = db.get_or_404(Tweet, tweet_id)
    if original_tweet.is_removed: abort(404)
    existing = Retweet.query.filter_by(user_id=current_user.id, tweet_id=original_tweet.id).first()
    if existing is None:
        db.session.add(Retweet(user_id=current_user.id, tweet_id=original_tweet.id))
        if original_tweet.user_id != current_user.id: db.session.add(Notification(user_id=original_tweet.user_id, message=f"{current_user.username} reposted your post"))
        db.session.commit(); flash("Post reposted.", "success")
    else:
        db.session.delete(existing); db.session.commit(); flash("Repost removed.", "success")
    return redirect(url_for("index"))


@login_required
def quote(tweet_id):
    original_tweet = db.get_or_404(Tweet, tweet_id)
    if original_tweet.is_removed: abort(404)
    response_intent = _tweet_conversation_intent(original_tweet)
    if request.method == "POST":
        content = request.form.get("content"); validation_error = validate_post_content(content, post_type="Quote")
        if validation_error: flash(validation_error, "danger"); return render_template("quote.html", tweet=original_tweet, response_intent=response_intent), 400
        db.session.add(Quote(content=content, user_id=current_user.id, tweet_id=original_tweet.id)); db.session.add(Notification(user_id=original_tweet.user_id, message=f"{current_user.username} quoted your post")); db.session.commit(); flash("Your quote has been posted!", "success"); return redirect(url_for("index"))
    return render_template("quote.html", tweet=original_tweet, response_intent=response_intent)


@login_required
def toggle_contribution(tweet_id, signal):
    if signal not in CONTRIBUTION_SIGNALS: abort(404)
    tweet = db.get_or_404(Tweet, tweet_id)
    if tweet.is_removed: abort(404)
    if tweet.user_id == current_user.id: flash("Constructive contribution signals are for recognizing someone else's post.", "warning"); return redirect(url_for("post_detail", tweet_id=tweet.id))
    existing = ConstructiveContribution.query.filter_by(user_id=current_user.id, tweet_id=tweet.id, signal=signal).first()
    if existing: db.session.delete(existing); flash(f"{CONTRIBUTION_SIGNALS[signal]} removed.", "success")
    else: db.session.add(ConstructiveContribution(user_id=current_user.id, tweet_id=tweet.id, signal=signal)); flash(f"Marked {CONTRIBUTION_SIGNALS[signal].lower()}.", "success")
    db.session.commit(); return redirect(url_for("post_detail", tweet_id=tweet.id))


@timeline_blueprint.record_once
def register_timeline_routes(state):
    state.app.add_url_rule("/", endpoint="index", view_func=index)
    state.app.add_url_rule("/post/<int:tweet_id>", endpoint="post_detail", view_func=post_detail)
    state.app.add_url_rule("/tweet", endpoint="tweet", view_func=tweet, methods=["POST"])
    state.app.add_url_rule("/post/<int:tweet_id>/topics", endpoint="update_post_topics", view_func=update_post_topics, methods=["POST"])
    state.app.add_url_rule("/uploads/<filename>", endpoint="uploaded_file", view_func=uploaded_file)
    state.app.add_url_rule("/retweet/<int:tweet_id>", endpoint="retweet", view_func=retweet, methods=["POST"])
    state.app.add_url_rule("/quote/<int:tweet_id>", endpoint="quote", view_func=quote, methods=["GET", "POST"])
    state.app.add_url_rule("/post/<int:tweet_id>/contribution/<signal>", endpoint="toggle_contribution", view_func=toggle_contribution, methods=["POST"])
