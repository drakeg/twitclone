"""Legacy compatibility module for TwitClone startup and public imports."""

import atexit
import os
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask

from config import Config
from twitclone.extensions import bcrypt, csrf, db, init_extensions, login_manager, migrate
from twitclone.models import (
    Bookmark,
    DirectMessage,
    Follows,
    Notification,
    Poll,
    PollOption,
    PollVote,
    Quote,
    Retweet,
    Tweet,
    User,
)
from twitclone.utils import (
    get_newest_users,
    get_trending_hashtags,
    gravatar,
    make_clickable_links,
    resize_image,
)


Config.validate()
app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
init_extensions(app)


def post_scheduled_tweets():
    now = datetime.utcnow()
    tweets = Tweet.query.filter(
        Tweet.scheduled_at <= now, Tweet.timestamp == None
    ).all()
    for scheduled_tweet in tweets:
        scheduled_tweet.timestamp = now
        db.session.commit()


scheduler = BackgroundScheduler()
if app.config["SCHEDULER_ENABLED"]:
    scheduler.add_job(
        func=post_scheduled_tweets,
        trigger=IntervalTrigger(seconds=app.config["SCHEDULER_INTERVAL_SECONDS"]),
        id="post_scheduled_tweets",
        name="Post scheduled tweets",
        replace_existing=True,
    )
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown() if scheduler.running else None)


@app.context_processor
def utility_processor():
    return {
        "gravatar": gravatar,
        "trending_hashtags": get_trending_hashtags(),
        "newest_users": get_newest_users(),
    }


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.template_filter("make_clickable")
def make_clickable_filter(value):
    return make_clickable_links(value)


if __name__ == "__main__":
    from twitclone import create_app

    create_app().run(
        debug=Config.ENVIRONMENT == "development",
        port=int(os.getenv("PORT", "8000")),
    )
