"""Scheduled-post processor tests."""

from datetime import datetime, timedelta

from twitclone.extensions import db
from twitclone.models import Tweet, User
from twitclone.scheduling import publish_due_tweets


def test_publisher_processes_only_due_tweets_and_is_idempotent(app):
    now = datetime(2026, 8, 15, 12, 0, 0)
    with app.app_context():
        user = User(username="alice", email="alice@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        due_at = now - timedelta(minutes=1)
        due = Tweet(content="due", user_id=user.id, scheduled_at=due_at)
        future = Tweet(content="future", user_id=user.id,
                       scheduled_at=now + timedelta(minutes=1))
        ordinary = Tweet(content="ordinary", user_id=user.id)
        db.session.add_all([due, future, ordinary])
        db.session.commit()
        due_id, future_id, ordinary_id = due.id, future.id, ordinary.id

        assert publish_due_tweets(now=now) == 1
        assert publish_due_tweets(now=now) == 0

        due = db.session.get(Tweet, due_id)
        future = db.session.get(Tweet, future_id)
        ordinary = db.session.get(Tweet, ordinary_id)
        assert due.scheduled_at is None
        assert due.timestamp == due_at
        assert future.scheduled_at == now + timedelta(minutes=1)
        assert ordinary.scheduled_at is None


def test_web_import_never_starts_scheduler():
    from app import scheduler

    assert scheduler.running is False
    assert scheduler.get_jobs() == []
