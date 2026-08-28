"""Regression coverage for author-controlled conversation health state."""

from twitclone.conversation_health import TweetConversationState
from twitclone.extensions import db
from twitclone.models import Quote, Tweet, User


def _user(app, username):
    with app.app_context():
        user = User(username=username, email=f"{username}@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        return user.id


def _tweet(app, author_id, content="Can anyone help with this?"):
    with app.app_context():
        tweet = Tweet(content=content, user_id=author_id)
        db.session.add(tweet)
        db.session.commit()
        return tweet.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_existing_posts_default_to_open_and_unresolved(client, app):
    author_id = _user(app, "author")
    tweet_id = _tweet(app, author_id)

    response = client.get(f"/post/{tweet_id}")

    assert response.status_code == 200
    assert b"Conversation open" in response.data
    assert b"Answered / resolved" not in response.data
    with app.app_context():
        assert db.session.get(TweetConversationState, tweet_id) is None


def test_author_can_close_and_reopen_without_deleting_existing_quotes(client, app):
    author_id = _user(app, "author")
    responder_id = _user(app, "responder")
    tweet_id = _tweet(app, author_id)
    with app.app_context():
        db.session.add(Quote(user_id=responder_id, tweet_id=tweet_id, content="Existing response"))
        db.session.commit()

    _login(client, author_id)
    close = client.post(
        f"/post/{tweet_id}/conversation-state",
        data={"action": "close"},
        follow_redirects=True,
    )
    assert b"Conversation closed" in close.data
    assert b"Existing responses remain visible" in close.data

    with app.app_context():
        state = db.session.get(TweetConversationState, tweet_id)
        assert state.is_closed is True
        assert Quote.query.filter_by(tweet_id=tweet_id).count() == 1

    reopen = client.post(
        f"/post/{tweet_id}/conversation-state",
        data={"action": "reopen"},
        follow_redirects=True,
    )
    assert b"Conversation open" in reopen.data
    with app.app_context():
        assert db.session.get(TweetConversationState, tweet_id).is_closed is False
        assert Quote.query.filter_by(tweet_id=tweet_id).count() == 1


def test_closed_conversation_blocks_direct_quote_requests(client, app):
    author_id = _user(app, "author")
    responder_id = _user(app, "responder")
    tweet_id = _tweet(app, author_id)
    with app.app_context():
        db.session.add(TweetConversationState(tweet_id=tweet_id, is_closed=True))
        db.session.commit()

    _login(client, responder_id)
    response = client.post(
        f"/quote/{tweet_id}",
        data={"content": "This should not be added"},
        follow_redirects=True,
    )

    assert b"closed this conversation to new quote responses" in response.data
    assert b'aria-label="Quote"' not in response.data
    with app.app_context():
        assert Quote.query.filter_by(tweet_id=tweet_id).count() == 0


def test_author_can_mark_resolved_and_clear_status(client, app):
    author_id = _user(app, "author")
    tweet_id = _tweet(app, author_id)
    _login(client, author_id)

    resolved = client.post(
        f"/post/{tweet_id}/conversation-state",
        data={"action": "resolve"},
        follow_redirects=True,
    )
    assert b"Answered / resolved" in resolved.data
    with app.app_context():
        assert db.session.get(TweetConversationState, tweet_id).is_resolved is True

    cleared = client.post(
        f"/post/{tweet_id}/conversation-state",
        data={"action": "unresolve"},
        follow_redirects=True,
    )
    assert b"Answered / resolved" not in cleared.data
    with app.app_context():
        assert db.session.get(TweetConversationState, tweet_id).is_resolved is False


def test_non_author_cannot_change_conversation_state(client, app):
    author_id = _user(app, "author")
    other_id = _user(app, "other")
    tweet_id = _tweet(app, author_id)
    _login(client, other_id)

    response = client.post(f"/post/{tweet_id}/conversation-state", data={"action": "close"})

    assert response.status_code == 403
    with app.app_context():
        assert db.session.get(TweetConversationState, tweet_id) is None


def test_timeline_surfaces_closed_and_resolved_state_and_hides_quote(client, app):
    author_id = _user(app, "author")
    tweet_id = _tweet(app, author_id, "A conversation with a final answer")
    with app.app_context():
        db.session.add(TweetConversationState(tweet_id=tweet_id, is_closed=True, is_resolved=True))
        db.session.commit()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Conversation closed" in response.data
    assert b"Answered / resolved" in response.data
    assert f'/quote/{tweet_id}'.encode() not in response.data
    assert f'/retweet/{tweet_id}'.encode() in response.data


def test_search_results_surface_conversation_state(client, app):
    author_id = _user(app, "author")
    viewer_id = _user(app, "viewer")
    tweet_id = _tweet(app, author_id, "Unique status search phrase")
    with app.app_context():
        db.session.add(TweetConversationState(tweet_id=tweet_id, is_closed=True, is_resolved=True))
        db.session.commit()
    _login(client, viewer_id)

    response = client.post("/search", data={"search_query": "Unique status search phrase"})

    assert response.status_code == 200
    assert b"Conversation closed" in response.data
    assert b"Answered / resolved" in response.data


def test_hashtag_results_surface_conversation_state(client, app):
    author_id = _user(app, "author")
    viewer_id = _user(app, "viewer")
    tweet_id = _tweet(app, author_id, "Status for #healthstate")
    with app.app_context():
        db.session.add(TweetConversationState(tweet_id=tweet_id, is_closed=True, is_resolved=True))
        db.session.commit()
    _login(client, viewer_id)

    response = client.get("/hashtag/healthstate")

    assert response.status_code == 200
    assert b"Conversation closed" in response.data
    assert b"Answered / resolved" in response.data
