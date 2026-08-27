"""Search, hashtag, and public discovery routes."""

from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from twitclone.discovery import discovery_blueprint
from twitclone.extensions import db
from twitclone.models import HashtagFollow, Tweet, User


def _normalize_hashtag(value: str) -> str:
    return value.strip().lstrip("#").lower()


def _normalize_search_query(value: str) -> str:
    return " ".join(value.strip().split())[:100]


def about():
    return render_template("about.html")


@login_required
def search():
    if request.method != "POST":
        return redirect(url_for("index"))

    search_query = _normalize_search_query(request.form.get("search_query", ""))
    if not search_query:
        return render_template(
            "search_results.html",
            search_query="",
            user_results=[],
            tweet_results=[],
            hashtag_name=None,
        )

    username_query = search_query.lstrip("@")
    hashtag_name = _normalize_hashtag(search_query) if search_query.startswith("#") else None
    text_query = search_query.lstrip("#") if hashtag_name else search_query

    user_results = (
        User.query.filter(
            or_(
                User.username.ilike(f"%{username_query}%"),
                User.bio.ilike(f"%{search_query}%"),
            )
        )
        .order_by(User.username.asc())
        .limit(25)
        .all()
    )
    tweet_results = (
        Tweet.query.filter(
            Tweet.content.ilike(f"%{text_query}%"),
            Tweet.is_removed.is_(False),
        )
        .order_by(Tweet.timestamp.desc())
        .limit(50)
        .all()
    )
    return render_template(
        "search_results.html",
        search_query=search_query,
        user_results=user_results,
        tweet_results=tweet_results,
        hashtag_name=hashtag_name,
    )


@login_required
def hashtag(hashtag):
    normalized = _normalize_hashtag(hashtag)
    tagged_hashtag = f"#{normalized}"
    tweets = (
        Tweet.query.filter(
            Tweet.content.ilike(f"%{tagged_hashtag}%"),
            Tweet.is_removed.is_(False),
        )
        .order_by(Tweet.timestamp.desc())
        .all()
    )
    is_following = (
        HashtagFollow.query.filter_by(user_id=current_user.id, hashtag=normalized).first()
        is not None
    )
    return render_template(
        "hashtag.html",
        hashtag=tagged_hashtag,
        hashtag_name=normalized,
        tweets=tweets,
        is_following=is_following,
    )


@login_required
def follow_hashtag(hashtag):
    normalized = _normalize_hashtag(hashtag)
    if normalized and not HashtagFollow.query.filter_by(
        user_id=current_user.id, hashtag=normalized
    ).first():
        db.session.add(HashtagFollow(user_id=current_user.id, hashtag=normalized))
        db.session.commit()
    return redirect(url_for("hashtag", hashtag=normalized))


@login_required
def unfollow_hashtag(hashtag):
    normalized = _normalize_hashtag(hashtag)
    followed = HashtagFollow.query.filter_by(
        user_id=current_user.id, hashtag=normalized
    ).first()
    if followed:
        db.session.delete(followed)
        db.session.commit()
    return redirect(url_for("hashtag", hashtag=normalized))


@discovery_blueprint.record_once
def register_discovery_routes(state):
    state.app.add_url_rule("/about", endpoint="about", view_func=about)
    state.app.add_url_rule(
        "/search", endpoint="search", view_func=search, methods=["GET", "POST"]
    )
    state.app.add_url_rule("/hashtag/<hashtag>", endpoint="hashtag", view_func=hashtag)
    state.app.add_url_rule(
        "/hashtag/<hashtag>/follow",
        endpoint="follow_hashtag",
        view_func=follow_hashtag,
        methods=["POST"],
    )
    state.app.add_url_rule(
        "/hashtag/<hashtag>/unfollow",
        endpoint="unfollow_hashtag",
        view_func=unfollow_hashtag,
        methods=["POST"],
    )
