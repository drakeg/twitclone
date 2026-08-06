"""Timeline and post routes."""

import os
from datetime import datetime

from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import text
from werkzeug.utils import secure_filename

from twitclone.extensions import db
from twitclone.models import (
    DirectMessage,
    Notification,
    Poll,
    PollVote,
    Quote,
    Retweet,
    Tweet,
    User,
)
from twitclone.timeline import timeline_blueprint
from twitclone.utils import get_newest_users, get_trending_hashtags, resize_image


def index():
    now = datetime.utcnow()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    tweets = db.session.query(
        Tweet.id.label("id"),
        Tweet.content.label("content"),
        Tweet.timestamp.label("timestamp"),
        Tweet.user_id.label("user_id"),
        db.literal(None).label("poll_id"),
        db.literal("tweet").label("type"),
    ).filter((Tweet.scheduled_at == None) | (Tweet.scheduled_at <= now))

    retweets = db.session.query(
        Retweet.id.label("id"),
        Retweet.tweet_id.label("content"),
        Retweet.timestamp.label("timestamp"),
        Retweet.user_id.label("user_id"),
        db.literal(None).label("poll_id"),
        db.literal("retweet").label("type"),
    )

    polls = db.session.query(
        Poll.id.label("id"),
        Poll.question.label("content"),
        Poll.created_at.label("timestamp"),
        Poll.user_id.label("user_id"),
        Poll.id.label("poll_id"),
        db.literal("poll").label("type"),
    )

    combined_query = tweets.union_all(retweets, polls).order_by(text("timestamp desc"))
    posts = combined_query.all()

    user_ids = {post.user_id for post in posts}
    users = {user.id: user for user in User.query.filter(User.id.in_(user_ids)).all()}

    posts_with_users = []
    for post in posts:
        post_dict = {
            "id": post.id,
            "content": post.content,
            "timestamp": post.timestamp,
            "user_id": post.user_id,
            "poll_id": post.poll_id,
            "type": post.type,
            "user": users[post.user_id],
        }
        if post.type == "poll":
            poll = Poll.query.get(post.poll_id)
            post_dict["poll"] = poll
            if current_user.is_authenticated:
                vote = PollVote.query.filter_by(
                    poll_id=post.poll_id, user_id=current_user.id
                ).first()
                post_dict["has_voted"] = vote is not None
            else:
                post_dict["has_voted"] = False
        posts_with_users.append(post_dict)

    return render_template(
        "index.html",
        posts=posts_with_users,
        current_time=current_time,
        trending_hashtags=get_trending_hashtags(),
        newest_users=get_newest_users(),
    )


@login_required
def tweet():
    content = request.form["content"]
    image = request.files.get("image")
    image_filename = None

    if image:
        image_filename = secure_filename(image.filename)
        image_path = os.path.join(current_app.config["UPLOAD_FOLDER"], image_filename)
        image.save(image_path)
        resized_image_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"], f"thumb_{image_filename}"
        )
        resize_image(image_path, resized_image_path)
        image_filename = f"thumb_{image_filename}"

    scheduled_date = request.form.get("scheduled_date")
    scheduled_time = request.form.get("scheduled_time")
    scheduled_at = None
    if scheduled_date and scheduled_time:
        scheduled_at = datetime.strptime(
            f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M"
        )

    if len(content) <= 144:
        if content.startswith("/dm "):
            dm_parts = content.split(" ", 2)
            if len(dm_parts) == 3:
                username = dm_parts[1]
                message = dm_parts[2]
                user = User.query.filter_by(username=username).first()
                if user:
                    dm = DirectMessage(
                        content=message,
                        sender_id=current_user.id,
                        receiver_id=user.id,
                    )
                    db.session.add(dm)
                    db.session.commit()
                    notification = Notification(
                        user_id=user.id,
                        message=f"{current_user.username} sent you a message",
                    )
                    db.session.add(notification)
                    db.session.commit()
                    flash("Your direct message has been sent!", "success")
                else:
                    flash("User not found.", "danger")
        else:
            new_tweet = Tweet(
                content=content,
                user_id=current_user.id,
                image=image_filename,
                scheduled_at=scheduled_at,
            )
            db.session.add(new_tweet)
            db.session.commit()
            if scheduled_at:
                flash("Your tweet has been scheduled!", "success")
            else:
                flash("Your tweet has been posted!", "success")
    else:
        flash("Tweet content exceeds 144 characters.", "danger")
    return redirect(url_for("index"))


def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@login_required
def retweet(tweet_id):
    original_tweet = Tweet.query.get_or_404(tweet_id)
    new_retweet = Retweet(user_id=current_user.id, tweet_id=original_tweet.id)
    db.session.add(new_retweet)
    db.session.commit()
    flash("You have retweeted this tweet!", "success")
    return redirect(url_for("index"))


@login_required
def quote(tweet_id):
    original_tweet = Tweet.query.get_or_404(tweet_id)
    if request.method == "POST":
        content = request.form["content"]
        if len(content) <= 144:
            new_quote = Quote(
                user_id=current_user.id,
                tweet_id=original_tweet.id,
                content=content,
            )
            db.session.add(new_quote)
            db.session.commit()
            flash("You have quoted this tweet!", "success")
            return redirect(url_for("index"))
        flash("Quote content exceeds 144 characters.", "danger")
    return render_template("quote.html", tweet=original_tweet)


@timeline_blueprint.record_once
def register_timeline_routes(state):
    """Register routes while retaining existing endpoint names."""
    state.app.add_url_rule("/", endpoint="index", view_func=index)
    state.app.add_url_rule("/tweet", endpoint="tweet", view_func=tweet, methods=["POST"])
    state.app.add_url_rule(
        "/uploads/<filename>", endpoint="uploaded_file", view_func=uploaded_file
    )
    state.app.add_url_rule(
        "/retweet/<int:tweet_id>",
        endpoint="retweet",
        view_func=retweet,
        methods=["POST"],
    )
    state.app.add_url_rule(
        "/quote/<int:tweet_id>",
        endpoint="quote",
        view_func=quote,
        methods=["GET", "POST"],
    )
