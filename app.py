"""Legacy compatibility module for TwitClone startup and public imports."""

import os

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_login import current_user

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
from twitclone.scheduling import publish_due_tweets


Config.validate()
app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
init_extensions(app)


def post_scheduled_tweets():
    """Compatibility wrapper for the package-owned worker operation."""
    return publish_due_tweets()


scheduler = BackgroundScheduler()


@app.context_processor
def utility_processor():
    unread_notification_count = 0
    unread_message_count = 0
    if current_user.is_authenticated:
        unread = Notification.query.filter_by(user_id=current_user.id, read=False)
        unread_notification_count = unread.count()
        unread_message_count = unread.filter(
            Notification.message.like("% sent you a message")
            | Notification.message.like("% replied to your message")
        ).count()

    return {
        "gravatar": gravatar,
        "trending_hashtags": get_trending_hashtags(),
        "newest_users": get_newest_users(),
        "unread_notification_count": unread_notification_count,
        "unread_message_count": unread_message_count,
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
