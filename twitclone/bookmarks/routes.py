"""Bookmark creation and listing routes."""

from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from twitclone.bookmarks import bookmarks_blueprint
from twitclone.extensions import db
from twitclone.models import Bookmark, Tweet


@login_required
def bookmark(tweet_id):
    tweet = Tweet.query.get_or_404(tweet_id)
    existing = Bookmark.query.filter_by(
        user_id=current_user.id, tweet_id=tweet.id
    ).first()
    if existing is None:
        new_bookmark = Bookmark(user_id=current_user.id, tweet_id=tweet.id)
        db.session.add(new_bookmark)
        db.session.commit()
    flash("Tweet has been bookmarked!", "success")
    return redirect(url_for("index"))


@login_required
def bookmarks():
    saved_bookmarks = (
        Bookmark.query.filter_by(user_id=current_user.id)
        .order_by(Bookmark.timestamp.desc())
        .all()
    )
    return render_template("bookmarks.html", bookmarks=saved_bookmarks)


@bookmarks_blueprint.record_once
def register_bookmark_routes(state):
    """Register routes while retaining existing endpoint names."""
    state.app.add_url_rule(
        "/bookmark/<int:tweet_id>",
        endpoint="bookmark",
        view_func=bookmark,
        methods=["POST"],
    )
    state.app.add_url_rule("/bookmarks", endpoint="bookmarks", view_func=bookmarks)
