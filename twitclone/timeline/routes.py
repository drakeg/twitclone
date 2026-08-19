"""Timeline and post routes."""

from datetime import UTC, datetime, timedelta

from flask import abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from twitclone.extensions import db
from twitclone.mentions import add_mention_notifications
from twitclone.models import DirectMessage, Notification, Quote, Retweet, Tweet, User
from twitclone.timeline import timeline_blueprint
from twitclone.timeline.media import store_image_upload
from twitclone.timeline.service import build_timeline_posts, paginate_timeline_posts
from twitclone.timeline.validation import validate_post_content
from twitclone.utils import get_newest_users, get_trending_hashtags


def index():
    now = datetime.now(UTC).replace(tzinfo=None)
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    posts = build_timeline_posts(now=now, viewer=current_user)
    page = request.args.get("page", default=1, type=int) or 1
    timeline_page = paginate_timeline_posts(posts, page=page)
    return render_template("index.html", posts=timeline_page.items, timeline_page=timeline_page, current_time=current_time, trending_hashtags=get_trending_hashtags(), newest_users=get_newest_users())


def post_detail(tweet_id):
    tweet = db.get_or_404(Tweet, tweet_id)
    now = datetime.now(UTC).replace(tzinfo=None)
    if tweet.is_removed or (tweet.scheduled_at is not None and tweet.scheduled_at > now):
        abort(404)
    return render_template("post_detail.html", tweet=tweet)


def _scheduled_at_from_form():
    scheduled_date = request.form.get("scheduled_date")
    scheduled_time = request.form.get("scheduled_time")
    if not scheduled_date and not scheduled_time:
        return None, None
    if not scheduled_date or not scheduled_time:
        return None, "Choose both a date and time to schedule a post."
    try:
        scheduled_at = datetime.strptime(f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None, "Choose a valid schedule date and time."
    now = datetime.now(UTC).replace(tzinfo=None)
    if scheduled_at <= now:
        return None, "Scheduled posts must be set for a future time."
    max_days = 90 if current_user.has_entitlement('ripple_plus') else 7
    if scheduled_at > now + timedelta(days=max_days):
        if max_days == 7:
            return None, "Free accounts can schedule up to 7 days ahead. Ripple+ extends scheduling to 90 days."
        return None, "Ripple+ posts can be scheduled up to 90 days ahead."
    return scheduled_at, None


@login_required
def tweet():
    content = request.form.get("content")
    validation_error = validate_post_content(content, post_type="Tweet")
    if validation_error:
        flash(validation_error, "danger"); return redirect(url_for("index"))
    image = request.files.get("image"); image_filename = None; original_image_filename = None
    if image and image.filename:
        image_error, original_image_filename, image_filename = store_image_upload(image, current_app.config["UPLOAD_FOLDER"])
        if image_error:
            flash(image_error, "danger"); return redirect(url_for("index"))
    scheduled_at, schedule_error = _scheduled_at_from_form()
    if schedule_error:
        flash(schedule_error, "danger"); return redirect(url_for("index"))
    if content.startswith("/dm "):
        dm_parts = content.split(" ", 2)
        if len(dm_parts) == 3:
            username, message = dm_parts[1], dm_parts[2]; user = User.query.filter_by(username=username).first()
            if user:
                db.session.add_all([DirectMessage(content=message, sender_id=current_user.id, receiver_id=user.id), Notification(user_id=user.id, message=f"{current_user.username} sent you a message")]); db.session.commit(); flash("Your direct message has been sent!", "success")
            else: flash("User not found.", "danger")
    else:
        new_tweet = Tweet(content=content, user_id=current_user.id, image=image_filename, original_image=original_image_filename, scheduled_at=scheduled_at)
        db.session.add(new_tweet); db.session.flush()
        if scheduled_at is None: add_mention_notifications(content=content, author=current_user, tweet_id=new_tweet.id)
        db.session.commit(); flash("Your tweet has been scheduled!" if scheduled_at else "Your tweet has been posted!", "success")
    return redirect(url_for("index"))


def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@login_required
def retweet(tweet_id):
    original_tweet = db.get_or_404(Tweet, tweet_id)
    if original_tweet.is_removed: abort(404)
    existing = Retweet.query.filter_by(user_id=current_user.id, tweet_id=original_tweet.id).first()
    if existing is None:
        db.session.add(Retweet(user_id=current_user.id, tweet_id=original_tweet.id))
        if original_tweet.user_id != current_user.id:
            db.session.add(Notification(user_id=original_tweet.user_id, message=f"{current_user.username} reposted your post", tweet_id=original_tweet.id))
        db.session.commit()
    flash("You have retweeted this tweet!", "success"); return redirect(url_for("index"))


@login_required
def quote(tweet_id):
    original_tweet = db.get_or_404(Tweet, tweet_id)
    if original_tweet.is_removed: abort(404)
    if request.method == "POST":
        content = request.form.get("content"); validation_error = validate_post_content(content, post_type="Quote")
        if validation_error:
            flash(validation_error, "danger"); return render_template("quote.html", tweet=original_tweet)
        db.session.add(Quote(user_id=current_user.id, tweet_id=original_tweet.id, content=content))
        if original_tweet.user_id != current_user.id:
            db.session.add(Notification(user_id=original_tweet.user_id, message=f"{current_user.username} quoted your post", tweet_id=original_tweet.id))
        db.session.commit(); flash("You have quoted this tweet!", "success"); return redirect(url_for("index"))
    return render_template("quote.html", tweet=original_tweet)


@timeline_blueprint.record_once
def register_timeline_routes(state):
    state.app.add_url_rule("/", endpoint="index", view_func=index)
    state.app.add_url_rule("/post/<int:tweet_id>", endpoint="post_detail", view_func=post_detail)
    state.app.add_url_rule("/tweet", endpoint="tweet", view_func=tweet, methods=["POST"])
    state.app.add_url_rule("/uploads/<filename>", endpoint="uploaded_file", view_func=uploaded_file)
    state.app.add_url_rule("/retweet/<int:tweet_id>", endpoint="retweet", view_func=retweet, methods=["POST"])
    state.app.add_url_rule("/quote/<int:tweet_id>", endpoint="quote", view_func=quote, methods=["GET", "POST"])
