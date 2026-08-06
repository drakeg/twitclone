"""Search and hashtag discovery routes."""

from flask import redirect, render_template, request, url_for
from flask_login import login_required

from twitclone.discovery import discovery_blueprint
from twitclone.models import Tweet, User


@login_required
def search():
    if request.method == "POST":
        search_query = request.form["search_query"]
        user_results = User.query.filter(
            User.username.ilike(f"%{search_query}%")
        ).all()
        tweet_results = Tweet.query.filter(
            Tweet.content.ilike(f"%#{search_query}%")
        ).all()
        return render_template(
            "search_results.html",
            search_query=search_query,
            user_results=user_results,
            tweet_results=tweet_results,
        )
    return redirect(url_for("index"))


@login_required
def hashtag(hashtag):
    tagged_hashtag = f"#{hashtag}"
    tweets = (
        Tweet.query.filter(Tweet.content.like(f"%{tagged_hashtag}%"))
        .order_by(Tweet.timestamp.desc())
        .all()
    )
    return render_template("hashtag.html", hashtag=tagged_hashtag, tweets=tweets)


@discovery_blueprint.record_once
def register_discovery_routes(state):
    """Register routes while retaining existing endpoint names."""
    state.app.add_url_rule(
        "/search", endpoint="search", view_func=search, methods=["GET", "POST"]
    )
    state.app.add_url_rule(
        "/hashtag/<hashtag>", endpoint="hashtag", view_func=hashtag
    )
