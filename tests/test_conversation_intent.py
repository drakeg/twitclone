"""Regression coverage for Sprint 9 intentional conversation metadata."""

from twitclone.conversation_models import TweetConversationIntent
from twitclone.extensions import db
from twitclone.models import Tweet, User
from twitclone.timeline.service import build_timeline_posts


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _user(app, username="intent_user"):
    with app.app_context():
        user = User(username=username, email=f"{username}@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        return user.id


def test_composer_exposes_intentional_conversation_choices(app, client):
    user_id = _user(app)
    _login(client, user_id)

    text = client.get("/").get_data(as_text=True)

    assert 'name="conversation_intent"' in text
    assert "Advice wanted" in text
    assert "Support wanted" in text
    assert "Respectful debate welcome" in text
    assert "Just sharing" in text
    assert "does not block respectful participation" in text


def test_post_persists_selected_conversation_intent(app, client):
    user_id = _user(app, "intent_author")
    _login(client, user_id)

    response = client.post(
        "/tweet",
        data={"content": "I could use some practical ideas", "conversation_intent": "advice"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    with app.app_context():
        tweet = Tweet.query.filter_by(user_id=user_id).one()
        record = TweetConversationIntent.query.filter_by(tweet_id=tweet.id).one()
        assert record.intent == "advice"


def test_unknown_conversation_intent_falls_back_to_open(app, client):
    user_id = _user(app, "intent_fallback")
    _login(client, user_id)

    client.post(
        "/tweet",
        data={"content": "Normal post", "conversation_intent": "hostile-mode"},
    )

    with app.app_context():
        tweet = Tweet.query.filter_by(user_id=user_id).one()
        assert TweetConversationIntent.query.filter_by(tweet_id=tweet.id).one().intent == "open"


def test_existing_posts_without_intent_record_render_as_open(app):
    user_id = _user(app, "legacy_intent")
    with app.app_context():
        tweet = Tweet(content="Older post", user_id=user_id)
        db.session.add(tweet)
        db.session.commit()

        from datetime import UTC, datetime

        post = next(item for item in build_timeline_posts(now=datetime.now(UTC).replace(tzinfo=None)) if item["type"] == "tweet")
        assert post["conversation_intent"]["key"] == "open"
        assert post["conversation_intent"]["label"] == "Open conversation"


def test_timeline_and_detail_show_selected_intent(app, client):
    user_id = _user(app, "intent_visible")
    _login(client, user_id)
    client.post(
        "/tweet",
        data={"content": "Having a rough day", "conversation_intent": "support"},
    )

    with app.app_context():
        tweet_id = Tweet.query.filter_by(user_id=user_id).one().id

    timeline = client.get("/").get_data(as_text=True)
    detail = client.get(f"/post/{tweet_id}").get_data(as_text=True)

    assert "Support wanted" in timeline
    assert "Respond with empathy and encouragement rather than debate." in timeline
    assert "Support wanted" in detail
