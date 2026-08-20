"""Conservative, deduplicated analytics event collection."""

from datetime import UTC, datetime
from uuid import uuid4

from flask import session
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from twitclone.analytics_models import FollowerSnapshot, PostImpression, ProfileVisit
from twitclone.extensions import db


def _today():
    return datetime.now(UTC).date()


def _viewer_identity(prefix):
    if current_user.is_authenticated:
        return current_user.id, f'user:{current_user.id}'
    key_name = f'analytics_{prefix}_visitor'
    token = session.get(key_name)
    if not token:
        token = uuid4().hex
        session[key_name] = token
    return None, f'anon:{token}'


def _safe_commit():
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


def record_post_impressions(posts):
    viewer_user_id, viewer_key = _viewer_identity('post')
    today = _today()
    seen = set()
    for post in posts:
        tweet_id = post.get('action_tweet_id')
        if not tweet_id or tweet_id in seen:
            continue
        seen.add(tweet_id)
        author_id = post.get('report_author_id')
        if not author_id or author_id == viewer_user_id:
            continue
        exists = PostImpression.query.filter_by(tweet_id=tweet_id, viewer_key=viewer_key, impression_date=today).first()
        if exists is None:
            db.session.add(PostImpression(tweet_id=tweet_id, author_id=author_id, viewer_user_id=viewer_user_id, viewer_key=viewer_key, impression_date=today))
    _safe_commit()


def record_post_impression(tweet):
    viewer_user_id, viewer_key = _viewer_identity('post')
    if viewer_user_id == tweet.user_id:
        return
    today = _today()
    if PostImpression.query.filter_by(tweet_id=tweet.id, viewer_key=viewer_key, impression_date=today).first() is None:
        db.session.add(PostImpression(tweet_id=tweet.id, author_id=tweet.user_id, viewer_user_id=viewer_user_id, viewer_key=viewer_key, impression_date=today))
        _safe_commit()


def record_profile_visit(profile_user):
    visitor_user_id, visitor_key = _viewer_identity('profile')
    if visitor_user_id == profile_user.id:
        return
    today = _today()
    if ProfileVisit.query.filter_by(profile_user_id=profile_user.id, visitor_key=visitor_key, visit_date=today).first() is None:
        db.session.add(ProfileVisit(profile_user_id=profile_user.id, visitor_user_id=visitor_user_id, visitor_key=visitor_key, visit_date=today))
        _safe_commit()


def snapshot_followers(user):
    today = _today()
    snapshot = FollowerSnapshot.query.filter_by(user_id=user.id, snapshot_date=today).first()
    count = user.followers.count()
    if snapshot is None:
        db.session.add(FollowerSnapshot(user_id=user.id, snapshot_date=today, follower_count=count))
    else:
        snapshot.follower_count = count
    _safe_commit()
