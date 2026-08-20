"""Regression coverage for Creator Pro measurement collection."""

from twitclone.analytics_models import FollowerSnapshot, PostImpression, ProfileVisit
from twitclone.extensions import db
from twitclone.models import Tweet, User


def _login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def test_timeline_impressions_are_daily_unique_and_exclude_author(app, client):
    with app.app_context():
        author = User(username='metric_author', email='metric_author@example.com', password='hash')
        viewer = User(username='metric_viewer', email='metric_viewer@example.com', password='hash')
        db.session.add_all([author, viewer]); db.session.commit()
        tweet = Tweet(content='Measure me', user_id=author.id); db.session.add(tweet); db.session.commit()
        author_id, viewer_id, tweet_id = author.id, viewer.id, tweet.id
    _login(client, viewer_id)
    assert client.get('/').status_code == 200
    assert client.get('/').status_code == 200
    with app.app_context():
        assert PostImpression.query.filter_by(tweet_id=tweet_id, viewer_user_id=viewer_id).count() == 1
    _login(client, author_id)
    assert client.get('/').status_code == 200
    with app.app_context():
        assert PostImpression.query.filter_by(tweet_id=tweet_id).count() == 1


def test_profile_visits_are_daily_unique_and_self_visits_do_not_count(app, client):
    with app.app_context():
        owner = User(username='profile_owner', email='profile_owner@example.com', password='hash')
        visitor = User(username='profile_visitor', email='profile_visitor@example.com', password='hash')
        db.session.add_all([owner, visitor]); db.session.commit(); owner_id, visitor_id = owner.id, visitor.id
    _login(client, visitor_id)
    client.get('/profile/profile_owner'); client.get('/profile/profile_owner')
    with app.app_context():
        assert ProfileVisit.query.filter_by(profile_user_id=owner_id, visitor_user_id=visitor_id).count() == 1
    _login(client, owner_id); client.get('/profile/profile_owner')
    with app.app_context():
        assert ProfileVisit.query.filter_by(profile_user_id=owner_id).count() == 1


def test_follow_and_unfollow_update_same_daily_snapshot(app, client):
    with app.app_context():
        target = User(username='snapshot_target', email='snapshot_target@example.com', password='hash')
        follower = User(username='snapshot_follower', email='snapshot_follower@example.com', password='hash')
        db.session.add_all([target, follower]); db.session.commit(); target_id, follower_id = target.id, follower.id
    _login(client, follower_id)
    response = client.post('/follow/snapshot_target'); assert response.status_code == 200
    with app.app_context():
        snapshot = FollowerSnapshot.query.filter_by(user_id=target_id).one(); assert snapshot.follower_count == 1
    response = client.post('/unfollow/snapshot_target'); assert response.status_code == 200
    with app.app_context():
        snapshot = FollowerSnapshot.query.filter_by(user_id=target_id).one(); assert snapshot.follower_count == 0
