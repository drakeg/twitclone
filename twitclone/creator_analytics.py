"""Creator Pro analytics reporting built from Ripple's persisted measurement data."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime, timedelta
import re

from sqlalchemy import false, func

from twitclone.analytics_models import FollowerSnapshot, PostImpression, ProfileVisit
from twitclone.extensions import db
from twitclone.models import Quote, Retweet, Tweet

ALLOWED_RANGES = {7, 30, 90}
HASHTAG_RE = re.compile(r"(?<!\w)#([A-Za-z0-9_]+)")


def _today() -> date:
    return datetime.now(UTC).date()


def _range_days(raw_value) -> int:
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        return 30
    return parsed if parsed in ALLOWED_RANGES else 30


def _window(days: int, *, today: date):
    start = today - timedelta(days=days - 1)
    previous_end = start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=days - 1)
    return start, today, previous_start, previous_end


def _first_tracking_date(user_id: int):
    candidates = [
        db.session.query(func.min(PostImpression.impression_date)).filter(PostImpression.author_id == user_id).scalar(),
        db.session.query(func.min(ProfileVisit.visit_date)).filter(ProfileVisit.profile_user_id == user_id).scalar(),
        db.session.query(func.min(FollowerSnapshot.snapshot_date)).filter(FollowerSnapshot.user_id == user_id).scalar(),
    ]
    candidates = [item for item in candidates if item is not None]
    return min(candidates) if candidates else None


def _count_impressions(user_id: int, start: date, end: date) -> int:
    return PostImpression.query.filter(
        PostImpression.author_id == user_id,
        PostImpression.impression_date >= start,
        PostImpression.impression_date <= end,
    ).count()


def _count_profile_visits(user_id: int, start: date, end: date) -> int:
    return ProfileVisit.query.filter(
        ProfileVisit.profile_user_id == user_id,
        ProfileVisit.visit_date >= start,
        ProfileVisit.visit_date <= end,
    ).count()


def _period_engagements(tweet_ids, start_date: date, end_date: date):
    if not tweet_ids:
        return 0, 0
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
    reposts = Retweet.query.filter(
        Retweet.tweet_id.in_(tweet_ids),
        Retweet.timestamp >= start_dt,
        Retweet.timestamp < end_dt,
    ).count()
    quotes = Quote.query.filter(
        Quote.tweet_id.in_(tweet_ids),
        Quote.is_removed.is_(False),
        Quote.timestamp >= start_dt,
        Quote.timestamp < end_dt,
    ).count()
    return reposts, quotes


def _follower_growth(user, start: date, end: date):
    baseline = FollowerSnapshot.query.filter(
        FollowerSnapshot.user_id == user.id,
        FollowerSnapshot.snapshot_date < start,
    ).order_by(FollowerSnapshot.snapshot_date.desc()).first()
    observed = FollowerSnapshot.query.filter(
        FollowerSnapshot.user_id == user.id,
        FollowerSnapshot.snapshot_date >= start,
        FollowerSnapshot.snapshot_date <= end,
    ).order_by(FollowerSnapshot.snapshot_date.asc()).all()

    if baseline is not None:
        start_count = baseline.follower_count
        complete = True
        baseline_date = baseline.snapshot_date
    elif observed:
        start_count = observed[0].follower_count
        complete = False
        baseline_date = observed[0].snapshot_date
    else:
        current_count = user.followers.count()
        return {
            'growth': 0,
            'start_count': current_count,
            'end_count': current_count,
            'baseline_date': None,
            'complete': False,
        }

    end_count = observed[-1].follower_count if observed else user.followers.count()
    return {
        'growth': end_count - start_count,
        'start_count': start_count,
        'end_count': end_count,
        'baseline_date': baseline_date,
        'complete': complete,
    }


def build_creator_dashboard(user, raw_days=None):
    days = _range_days(raw_days)
    today = _today()
    start, end, previous_start, previous_end = _window(days, today=today)
    tweets = Tweet.query.filter_by(user_id=user.id, is_removed=False).all()
    tweet_ids = [tweet.id for tweet in tweets]

    impressions = _count_impressions(user.id, start, end)
    profile_visits = _count_profile_visits(user.id, start, end)
    previous_impressions = _count_impressions(user.id, previous_start, previous_end)
    previous_profile_visits = _count_profile_visits(user.id, previous_start, previous_end)
    reposts, quotes = _period_engagements(tweet_ids, start, end)
    previous_reposts, previous_quotes = _period_engagements(tweet_ids, previous_start, previous_end)
    engagements = reposts + quotes
    previous_engagements = previous_reposts + previous_quotes
    engagement_rate = round((engagements / impressions) * 100, 2) if impressions else 0
    previous_engagement_rate = round((previous_engagements / previous_impressions) * 100, 2) if previous_impressions else 0

    first_tracking_date = _first_tracking_date(user.id)
    current_complete = bool(first_tracking_date and first_tracking_date <= start)
    previous_complete = bool(first_tracking_date and first_tracking_date <= previous_start)

    impression_counts = Counter(dict(
        db.session.query(PostImpression.tweet_id, func.count(PostImpression.id))
        .filter(
            PostImpression.author_id == user.id,
            PostImpression.impression_date >= start,
            PostImpression.impression_date <= end,
        )
        .group_by(PostImpression.tweet_id)
        .all()
    ))
    id_filter = Retweet.tweet_id.in_(tweet_ids) if tweet_ids else false()
    repost_counts = Counter(dict(
        db.session.query(Retweet.tweet_id, func.count(Retweet.id))
        .filter(
            id_filter,
            Retweet.timestamp >= datetime.combine(start, datetime.min.time()),
            Retweet.timestamp < datetime.combine(end + timedelta(days=1), datetime.min.time()),
        )
        .group_by(Retweet.tweet_id)
        .all()
    ))
    quote_filter = Quote.tweet_id.in_(tweet_ids) if tweet_ids else false()
    quote_counts = Counter(dict(
        db.session.query(Quote.tweet_id, func.count(Quote.id))
        .filter(
            quote_filter,
            Quote.is_removed.is_(False),
            Quote.timestamp >= datetime.combine(start, datetime.min.time()),
            Quote.timestamp < datetime.combine(end + timedelta(days=1), datetime.min.time()),
        )
        .group_by(Quote.tweet_id)
        .all()
    ))

    post_performance = []
    hashtag_posts = Counter()
    hashtag_impressions = Counter()
    hashtag_engagements = Counter()
    for tweet in sorted(tweets, key=lambda item: item.timestamp, reverse=True):
        post_impressions = impression_counts[tweet.id]
        post_reposts = repost_counts[tweet.id]
        post_quotes = quote_counts[tweet.id]
        post_engagements = post_reposts + post_quotes
        post_rate = round((post_engagements / post_impressions) * 100, 2) if post_impressions else 0
        post_performance.append({
            'tweet': tweet,
            'impressions': post_impressions,
            'reposts': post_reposts,
            'quotes': post_quotes,
            'engagements': post_engagements,
            'engagement_rate': post_rate,
        })
        tags = {tag.lower() for tag in HASHTAG_RE.findall(tweet.content or '')}
        for tag in tags:
            hashtag_posts[tag] += 1
            hashtag_impressions[tag] += post_impressions
            hashtag_engagements[tag] += post_engagements

    hashtag_performance = []
    for tag, post_count in hashtag_posts.most_common():
        tag_impressions = hashtag_impressions[tag]
        tag_engagements = hashtag_engagements[tag]
        hashtag_performance.append({
            'tag': tag,
            'posts': post_count,
            'impressions': tag_impressions,
            'engagements': tag_engagements,
            'engagement_rate': round((tag_engagements / tag_impressions) * 100, 2) if tag_impressions else 0,
        })

    return {
        'days': days,
        'range_start': start,
        'range_end': end,
        'first_tracking_date': first_tracking_date,
        'current_complete': current_complete,
        'previous_complete': previous_complete,
        'stats': {
            'followers': user.followers.count(),
            'impressions': impressions,
            'profile_visits': profile_visits,
            'reposts': reposts,
            'quotes': quotes,
            'engagements': engagements,
            'engagement_rate': engagement_rate,
        },
        'previous': {
            'impressions': previous_impressions,
            'profile_visits': previous_profile_visits,
            'engagements': previous_engagements,
            'engagement_rate': previous_engagement_rate,
        },
        'follower_growth': _follower_growth(user, start, end),
        'post_performance': post_performance,
        'hashtag_performance': hashtag_performance,
    }


__all__ = ['ALLOWED_RANGES', 'build_creator_dashboard']
