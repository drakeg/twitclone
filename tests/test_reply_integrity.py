"""Sprint 14 Story 14.5 reply integrity and compatibility coverage."""

from twitclone.extensions import db
from twitclone.models import Quote, Tweet, User
from twitclone.reply_models import Reply, ReplyContribution
from twitclone.replies.routes import MAX_REPLY_DEPTH


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


def test_nested_reply_depth_is_server_side_bounded(client, app):
    author_id = _user(app, "integrity_depth_author")
    replier_id = _user(app, "integrity_depth_replier")
    with app.app_context():
        tweet = Tweet(content="depth integrity root", user_id=author_id)
        db.session.add(tweet)
        db.session.flush()
        parent = Reply(tweet_id=tweet.id, user_id=author_id, content="depth 0")
        db.session.add(parent)
        db.session.flush()
        for depth in range(1, MAX_REPLY_DEPTH + 1):
            parent = Reply(
                tweet_id=tweet.id,
                user_id=author_id,
                parent_reply_id=parent.id,
                content=f"depth {depth}",
            )
            db.session.add(parent)
            db.session.flush()
        db.session.commit()
        tweet_id, parent_id = tweet.id, parent.id
        before_count = Reply.query.filter_by(tweet_id=tweet.id).count()

    _login(client, replier_id)
    response = client.post(
        f"/post/{tweet_id}/reply/{parent_id}/replies",
        data={"content": "must not exceed depth cap"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"maximum nesting depth" in response.data.lower()
    with app.app_context():
        assert Reply.query.filter_by(tweet_id=tweet_id).count() == before_count
        assert Reply.query.filter_by(content="must not exceed depth cap").first() is None


def test_removed_parent_is_tombstoned_without_broken_permalink_or_identity_leak(client, app):
    root_author_id = _user(app, "integrity_root_author")
    removed_author_id = _user(app, "integrity_removed_parent")
    child_author_id = _user(app, "integrity_child_author")
    with app.app_context():
        tweet = Tweet(content="removal integrity root", user_id=root_author_id)
        db.session.add(tweet)
        db.session.flush()
        parent = Reply(
            tweet_id=tweet.id,
            user_id=removed_author_id,
            content="removed parent secret text",
            is_removed=True,
            removal_reason="moderated",
        )
        db.session.add(parent)
        db.session.flush()
        child = Reply(
            tweet_id=tweet.id,
            user_id=child_author_id,
            parent_reply_id=parent.id,
            content="visible child survives",
        )
        db.session.add(child)
        db.session.commit()
        tweet_id, parent_id = tweet.id, parent.id

    response = client.get(f"/post/{tweet_id}/thread")
    assert response.status_code == 200
    assert b"visible child survives" in response.data
    assert b"Replying to a removed reply" in response.data
    assert b"removed parent secret text" not in response.data
    assert b"@integrity_removed_parent" not in response.data
    assert f"reply/{parent_id}".encode() not in response.data


def test_contribution_toggle_exposes_accessible_pressed_state(client, app):
    author_id = _user(app, "integrity_signal_author")
    viewer_id = _user(app, "integrity_signal_viewer")
    with app.app_context():
        tweet = Tweet(content="signal integrity root", user_id=author_id)
        db.session.add(tweet)
        db.session.flush()
        reply = Reply(tweet_id=tweet.id, user_id=author_id, content="signal target")
        db.session.add(reply)
        db.session.commit()
        tweet_id, reply_id = tweet.id, reply.id

    _login(client, viewer_id)
    response = client.get(f"/post/{tweet_id}/thread")
    assert response.status_code == 200
    assert b'aria-pressed="false"' in response.data

    with app.app_context():
        db.session.add(ReplyContribution(user_id=viewer_id, reply_id=reply_id, signal="helpful"))
        db.session.commit()

    response = client.get(f"/post/{tweet_id}/thread")
    assert b'aria-pressed="true"' in response.data
    assert b"Helpful 1" in response.data


def test_historical_quotes_remain_distinct_from_reply_thread(client, app):
    author_id = _user(app, "integrity_quote_author")
    responder_id = _user(app, "integrity_quote_responder")
    with app.app_context():
        tweet = Tweet(content="quote compatibility root", user_id=author_id)
        db.session.add(tweet)
        db.session.flush()
        db.session.add(Reply(tweet_id=tweet.id, user_id=responder_id, content="real public reply"))
        db.session.add(Quote(tweet_id=tweet.id, user_id=responder_id, content="historical quote stays quote"))
        db.session.commit()
        tweet_id = tweet.id

    response = client.get(f"/post/{tweet_id}/thread")
    assert response.status_code == 200
    assert b"real public reply" in response.data
    assert b"historical quote stays quote" not in response.data
    with app.app_context():
        assert Reply.query.filter_by(tweet_id=tweet_id).count() == 1
        assert Quote.query.filter_by(tweet_id=tweet_id).count() == 1
