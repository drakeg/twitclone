"""Sprint 14 Story 14.2 threaded reply structure coverage."""

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


def test_nested_reply_persists_parent_and_targets_parent_author(client, app):
    root_author_id = _user(app, "nested_root_author")
    parent_author_id = _user(app, "nested_parent_author")
    child_author_id = _user(app, "nested_child_author")
    with app.app_context():
        tweet = Tweet(content="nested root", user_id=root_author_id)
        db.session.add(tweet)
        db.session.flush()
        parent = Reply(tweet_id=tweet.id, user_id=parent_author_id, content="parent reply")
        db.session.add(parent)
        db.session.commit()
        tweet_id, parent_id = tweet.id, parent.id

    _login(client, child_author_id)
    response = client.post(
        f"/post/{tweet_id}/reply/{parent_id}/replies",
        data={"content": "child reply"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    with app.app_context():
        child = Reply.query.filter_by(content="child reply").one()
        assert child.parent_reply_id == parent_id
        assert child.tweet_id == tweet_id


def test_nested_reply_parent_must_belong_to_same_root(client, app):
    author_id = _user(app, "cross_root_author")
    replier_id = _user(app, "cross_root_replier")
    with app.app_context():
        first = Tweet(content="first root", user_id=author_id)
        second = Tweet(content="second root", user_id=author_id)
        db.session.add_all([first, second])
        db.session.flush()
        parent = Reply(tweet_id=second.id, user_id=author_id, content="other root reply")
        db.session.add(parent)
        db.session.commit()
        first_id, parent_id = first.id, parent.id

    _login(client, replier_id)
    response = client.post(
        f"/post/{first_id}/reply/{parent_id}/replies",
        data={"content": "must fail"},
    )
    assert response.status_code == 404


def test_thread_renders_depth_first_with_parent_navigation(client, app):
    author_id = _user(app, "tree_author")
    other_id = _user(app, "tree_other")
    with app.app_context():
        tweet = Tweet(content="tree root", user_id=author_id)
        db.session.add(tweet)
        db.session.flush()
        first = Reply(tweet_id=tweet.id, user_id=other_id, content="first root reply")
        second = Reply(tweet_id=tweet.id, user_id=author_id, content="second root reply")
        db.session.add_all([first, second])
        db.session.flush()
        child = Reply(tweet_id=tweet.id, user_id=author_id, parent_reply_id=first.id, content="first child")
        db.session.add(child)
        db.session.commit()
        tweet_id = tweet.id

    response = client.get(f"/post/{tweet_id}/thread")
    assert response.status_code == 200
    assert response.data.index(b"first root reply") < response.data.index(b"first child") < response.data.index(b"second root reply")
    assert b"Replying to" in response.data
    assert b"@tree_other" in response.data


def test_visual_nesting_is_bounded_but_deep_parent_chain_is_preserved(client, app):
    author_id = _user(app, "deep_author")
    with app.app_context():
        tweet = Tweet(content="deep root", user_id=author_id)
        db.session.add(tweet)
        db.session.flush()
        parent = None
        for number in range(5):
            reply = Reply(
                tweet_id=tweet.id,
                user_id=author_id,
                parent_reply_id=parent.id if parent else None,
                content=f"depth {number}",
            )
            db.session.add(reply)
            db.session.flush()
            parent = reply
        db.session.commit()
        tweet_id = tweet.id

    response = client.get(f"/post/{tweet_id}/thread")
    assert response.status_code == 200
    assert b"depth 4" in response.data
    assert b"deeper thread" in response.data
    assert b"margin-left: 4.5rem" in response.data


def test_closed_conversation_blocks_nested_reply(client, app):
    from twitclone.conversation_health import TweetConversationState

    author_id = _user(app, "nested_closed_author")
    replier_id = _user(app, "nested_closed_replier")
    with app.app_context():
        tweet = Tweet(content="closed nested root", user_id=author_id)
        db.session.add(tweet)
        db.session.flush()
        parent = Reply(tweet_id=tweet.id, user_id=author_id, content="existing parent")
        db.session.add(parent)
        db.session.add(TweetConversationState(tweet_id=tweet.id, is_closed=True, is_resolved=False))
        db.session.commit()
        tweet_id, parent_id = tweet.id, parent.id

    _login(client, replier_id)
    response = client.post(
        f"/post/{tweet_id}/reply/{parent_id}/replies",
        data={"content": "blocked nested reply"},
    )
    assert response.status_code == 409
