"""Sprint 14 Story 14.1 public reply foundation coverage."""

from twitclone.extensions import db
from twitclone.models import Quote, Tweet, User
from twitclone.reply_models import Reply


def _user(app, username):
    with app.app_context():
        user = User(username=username, email=f"{username}@example.com", password="hash")
        db.session.add(user); db.session.commit(); return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id); session["_fresh"] = True


def test_authenticated_user_can_create_public_reply_with_stable_permalink(client, app):
    author_id = _user(app, "reply_author")
    replier_id = _user(app, "reply_writer")
    with app.app_context():
        tweet = Tweet(content="root post", user_id=author_id); db.session.add(tweet); db.session.commit(); tweet_id = tweet.id
    _login(client, replier_id)
    response = client.post(f"/post/{tweet_id}/replies", data={"content": "public answer"}, follow_redirects=False)
    assert response.status_code == 302
    with app.app_context():
        reply = Reply.query.filter_by(tweet_id=tweet_id).one()
        assert reply.content == "public answer"
        reply_id = reply.id
    assert response.headers["Location"].endswith(f"/post/{tweet_id}/reply/{reply_id}")
    permalink = client.get(response.headers["Location"], follow_redirects=True)
    assert b"public answer" in permalink.data


def test_reply_thread_is_oldest_first_and_quote_history_is_not_reinterpreted(client, app):
    author_id = _user(app, "thread_author")
    other_id = _user(app, "thread_other")
    with app.app_context():
        tweet = Tweet(content="thread root", user_id=author_id); db.session.add(tweet); db.session.flush()
        db.session.add_all([Reply(tweet_id=tweet.id, user_id=other_id, content="first"), Reply(tweet_id=tweet.id, user_id=author_id, content="second"), Quote(tweet_id=tweet.id, user_id=other_id, content="historical quote")]); db.session.commit(); tweet_id = tweet.id
    response = client.get(f"/post/{tweet_id}/thread")
    assert response.status_code == 200
    assert response.data.index(b"first") < response.data.index(b"second")
    assert b"historical quote" not in response.data


def test_closed_conversation_rejects_new_reply_but_keeps_existing_reply_readable(client, app):
    from twitclone.conversation_health import TweetConversationState
    author_id = _user(app, "closed_author")
    replier_id = _user(app, "closed_replier")
    with app.app_context():
        tweet = Tweet(content="closed root", user_id=author_id); db.session.add(tweet); db.session.flush()
        db.session.add(Reply(tweet_id=tweet.id, user_id=replier_id, content="existing reply")); db.session.add(TweetConversationState(tweet_id=tweet.id, is_closed=True, is_resolved=False)); db.session.commit(); tweet_id = tweet.id
    _login(client, replier_id)
    response = client.post(f"/post/{tweet_id}/replies", data={"content": "blocked"})
    assert response.status_code == 409
    thread = client.get(f"/post/{tweet_id}/thread")
    assert b"existing reply" in thread.data
    assert b"Conversation closed" in thread.data


def test_space_scoped_post_does_not_leak_into_global_reply_thread(client, app):
    from twitclone.spaces.models import Space, SpaceMembership, SpacePost
    author_id = _user(app, "space_reply_author")
    with app.app_context():
        space = Space(name="Reply Space", slug="reply-space", description="scope", owner_id=author_id); db.session.add(space); db.session.flush()
        db.session.add(SpaceMembership(space_id=space.id, user_id=author_id, role="owner")); tweet = Tweet(content="space root", user_id=author_id); db.session.add(tweet); db.session.flush(); db.session.add(SpacePost(space_id=space.id, tweet_id=tweet.id, user_id=author_id)); db.session.commit(); tweet_id = tweet.id
    assert client.get(f"/post/{tweet_id}/thread").status_code == 404
