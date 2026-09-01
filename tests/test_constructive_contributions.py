from twitclone.contribution_models import ConstructiveContribution
from twitclone.extensions import db
from twitclone.models import Tweet, User


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _users_and_tweet(app):
    with app.app_context():
        alice = User(username="alice", email="alice@example.com", password="hash")
        bob = User(username="bob", email="bob@example.com", password="hash")
        db.session.add_all([alice, bob]); db.session.flush()
        tweet = Tweet(content="A constructive contribution.", user_id=bob.id)
        db.session.add(tweet); db.session.commit()
        return alice.id, bob.id, tweet.id


def test_user_can_toggle_constructive_signal(client, app):
    alice_id, _, tweet_id = _users_and_tweet(app); _login(client, alice_id)
    response = client.post(f"/post/{tweet_id}/contribution/helpful", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert ConstructiveContribution.query.filter_by(tweet_id=tweet_id, signal="helpful").count() == 1
    client.post(f"/post/{tweet_id}/contribution/helpful", follow_redirects=True)
    with app.app_context():
        assert ConstructiveContribution.query.filter_by(tweet_id=tweet_id, signal="helpful").count() == 0


def test_user_cannot_signal_own_post(client, app):
    _, bob_id, tweet_id = _users_and_tweet(app); _login(client, bob_id)
    response = client.post(f"/post/{tweet_id}/contribution/thoughtful", follow_redirects=True)
    assert b"for recognizing someone else" in response.data
    with app.app_context():
        assert ConstructiveContribution.query.filter_by(tweet_id=tweet_id).count() == 0


def test_unknown_signal_is_rejected(client, app):
    alice_id, _, tweet_id = _users_and_tweet(app); _login(client, alice_id)
    assert client.post(f"/post/{tweet_id}/contribution/like").status_code == 404


def test_post_detail_explains_constructive_signals(client, app):
    alice_id, _, tweet_id = _users_and_tweet(app); _login(client, alice_id)
    response = client.get(f"/post/{tweet_id}")
    assert b"Helpful" in response.data
    assert b"Thoughtful" in response.data
    assert b"Useful context" in response.data
    assert b"not a single popularity score" in response.data
