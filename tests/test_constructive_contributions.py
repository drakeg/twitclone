from twitclone.contribution_models import ConstructiveContribution
from twitclone.extensions import db
from twitclone.models import Tweet


def _login(client, username="testuser", password="password"):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=True)


def test_user_can_toggle_constructive_signal(client, app, second_user):
    with app.app_context():
        tweet = Tweet.query.filter(Tweet.user_id == second_user.id).first()
        tweet_id = tweet.id
    _login(client)
    response = client.post(f"/post/{tweet_id}/contribution/helpful", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert ConstructiveContribution.query.filter_by(tweet_id=tweet_id, signal="helpful").count() == 1
    client.post(f"/post/{tweet_id}/contribution/helpful", follow_redirects=True)
    with app.app_context():
        assert ConstructiveContribution.query.filter_by(tweet_id=tweet_id, signal="helpful").count() == 0


def test_user_cannot_signal_own_post(client, app):
    _login(client)
    with app.app_context():
        tweet = Tweet.query.filter_by(user_id=1).first()
        tweet_id = tweet.id
    response = client.post(f"/post/{tweet_id}/contribution/thoughtful", follow_redirects=True)
    assert b"for recognizing someone else" in response.data
    with app.app_context():
        assert ConstructiveContribution.query.filter_by(tweet_id=tweet_id).count() == 0


def test_unknown_signal_is_rejected(client, app, second_user):
    with app.app_context():
        tweet_id = Tweet.query.filter(Tweet.user_id == second_user.id).first().id
    _login(client)
    assert client.post(f"/post/{tweet_id}/contribution/like").status_code == 404


def test_post_detail_explains_constructive_signals(client, app, second_user):
    with app.app_context():
        tweet_id = Tweet.query.filter(Tweet.user_id == second_user.id).first().id
    _login(client)
    response = client.get(f"/post/{tweet_id}")
    assert b"Helpful" in response.data
    assert b"Thoughtful" in response.data
    assert b"Useful context" in response.data
    assert b"not a single popularity score" in response.data
