"""Sprint 14 Story 14.3 conversation intent and health semantics coverage."""

from twitclone.conversation_health import TweetConversationState
from twitclone.conversation_models import TweetConversationIntent
from twitclone.extensions import db
from twitclone.models import Tweet, User
from twitclone.reply_models import Reply


def _user(app, username):
    with app.app_context():
        user = User(username=username, email=f"{username}@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_thread_explains_root_intent_for_top_level_and_nested_replies(client, app):
    author_id = _user(app, "intent_author")
    replier_id = _user(app, "intent_replier")
    with app.app_context():
        tweet = Tweet(content="Need practical help", user_id=author_id)
        db.session.add(tweet)
        db.session.flush()
        db.session.add(TweetConversationIntent(tweet_id=tweet.id, intent="advice"))
        db.session.add(Reply(tweet_id=tweet.id, user_id=replier_id, content="first suggestion"))
        db.session.commit()
        tweet_id = tweet.id

    _login(client, replier_id)
    response = client.get(f"/post/{tweet_id}/thread")
    assert response.status_code == 200
    assert b"Conversation expectations" in response.data
    assert b"Advice wanted" in response.data
    assert b"Offer practical suggestions or relevant experience." in response.data
    assert b"This expectation comes from the root post and applies throughout the reply thread." in response.data
    assert b"Thread expectation: Advice wanted" in response.data


def test_resolved_conversation_remains_replyable_and_explains_status(client, app):
    author_id = _user(app, "resolved_author")
    replier_id = _user(app, "resolved_replier")
    with app.app_context():
        tweet = Tweet(content="Question with answer", user_id=author_id)
        db.session.add(tweet)
        db.session.flush()
        db.session.add(TweetConversationState(tweet_id=tweet.id, is_closed=False, is_resolved=True))
        db.session.commit()
        tweet_id = tweet.id

    _login(client, replier_id)
    page = client.get(f"/post/{tweet_id}/thread")
    assert page.status_code == 200
    assert b"Answered / resolved" in page.data
    assert b"is informational" in page.data
    assert b"Reply to the post" in page.data

    posted = client.post(f"/post/{tweet_id}/replies", data={"content": "one more useful detail"}, follow_redirects=False)
    assert posted.status_code == 302
    with app.app_context():
        assert Reply.query.filter_by(tweet_id=tweet_id, content="one more useful detail").one() is not None


def test_closed_and_resolved_conversation_still_blocks_new_replies(client, app):
    author_id = _user(app, "closed_resolved_author")
    replier_id = _user(app, "closed_resolved_replier")
    with app.app_context():
        tweet = Tweet(content="Finished discussion", user_id=author_id)
        db.session.add(tweet)
        db.session.flush()
        existing = Reply(tweet_id=tweet.id, user_id=replier_id, content="existing reply")
        db.session.add(existing)
        db.session.add(TweetConversationState(tweet_id=tweet.id, is_closed=True, is_resolved=True))
        db.session.commit()
        tweet_id, existing_id = tweet.id, existing.id

    _login(client, replier_id)
    page = client.get(f"/post/{tweet_id}/thread")
    assert page.status_code == 200
    assert b"Conversation closed" in page.data
    assert b"Answered / resolved" in page.data
    assert b"Existing replies remain readable" in page.data
    assert b"existing reply" in page.data
    assert b"Reply to the post" not in page.data

    top_level = client.post(f"/post/{tweet_id}/replies", data={"content": "blocked top-level"})
    nested = client.post(f"/post/{tweet_id}/reply/{existing_id}/replies", data={"content": "blocked child"})
    assert top_level.status_code == 409
    assert nested.status_code == 409
