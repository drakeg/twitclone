"""Bookmark creation and listing routes."""

from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from twitclone.bookmarks import bookmarks_blueprint
from twitclone.extensions import db
from twitclone.models import Bookmark, Tweet


@login_required
def bookmark(tweet_id):
    tweet = db.get_or_404(Tweet, tweet_id)
    if tweet.is_removed:
        abort(404)
    existing = Bookmark.query.filter_by(user_id=current_user.id, tweet_id=tweet.id).first()
    if existing is None:
        db.session.add(Bookmark(user_id=current_user.id, tweet_id=tweet.id))
        db.session.commit()
    flash("Tweet has been bookmarked!", "success")
    return redirect(url_for("index"))


@login_required
def bookmarks():
    saved_bookmarks = (
        Bookmark.query.join(Bookmark.tweet)
        .filter(Bookmark.user_id == current_user.id, Tweet.is_removed.is_(False))
        .order_by(Bookmark.timestamp.desc())
        .all()
    )
    return render_template("bookmarks.html", bookmarks=saved_bookmarks)


@bookmarks_blueprint.record_once
def register_bookmark_routes(state):
    state.app.add_url_rule("/bookmark/<int:tweet_id>", endpoint="bookmark", view_func=bookmark, methods=["POST"])
    state.app.add_url_rule("/bookmarks", endpoint="bookmarks", view_func=bookmarks)
