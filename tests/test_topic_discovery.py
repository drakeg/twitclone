"""Sprint 10 Story 10.4 topic discovery regression coverage."""

from twitclone.contribution_models import ConstructiveContribution
from twitclone.extensions import db
from twitclone.models import Entitlement, Tweet, User
from twitclone.topic_discovery import topic_contributors
from twitclone.topic_models import Topic, TweetTopic


def _user(username):
    user = User(username=username, email=f"{username}@example.com", password="hash")
    db.session.add(user)
    db.session.flush()
    return user


def _explicit_post(user, topic, content):
    tweet = Tweet(content=content, user_id=user.id)
    db.session.add(tweet)
    db.session.flush()
    db.session.add(TweetTopic(tweet_id=tweet.id, topic_id=topic.id, source="explicit"))
    return tweet


def _recognize(recognizer, tweet, signal="helpful"):
    db.session.add(
        ConstructiveContribution(user_id=recognizer.id, tweet_id=tweet.id, signal=signal)
    )


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_topic_discovery_orders_by_visible_evidence_not_popularity_or_payment(app):
    with app.app_context():
        topic = Topic(name="AWS", slug="aws")
        alice = _user("alice")
        bob = _user("bob")
        viewers = [_user(f"reviewer{i}") for i in range(1, 5)]
        followers = [_user(f"follower{i}") for i in range(1, 6)]
        db.session.add(topic)
        db.session.flush()

        alice_posts = [_explicit_post(alice, topic, f"Alice AWS post {i}") for i in range(3)]
        bob_post = _explicit_post(bob, topic, "Bob AWS post")

        _recognize(viewers[0], alice_posts[0], "helpful")
        _recognize(viewers[0], alice_posts[0], "thoughtful")
        _recognize(viewers[1], alice_posts[1], "helpful")
        _recognize(viewers[2], alice_posts[2], "context")
        _recognize(viewers[2], alice_posts[2], "thoughtful")
        _recognize(viewers[3], bob_post, "helpful")

        for follower in followers:
            follower.followed.append(bob)
        db.session.add(Entitlement(user_id=bob.id, key="ripple_plus", active=True, source="subscription"))
        db.session.commit()

        discovered_topic, contributors = topic_contributors("aws")

        assert discovered_topic.id == topic.id
        assert [item["user"].username for item in contributors] == ["alice", "bob"]
        assert contributors[0]["summary"]["level"] == "Established contributor"
        assert contributors[1]["summary"]["level"] == "Emerging contributor"


def test_hashtag_only_and_removed_posts_do_not_qualify_for_topic_discovery(app):
    with app.app_context():
        topic = Topic(name="Python", slug="python")
        explicit_user = _user("explicit_user")
        hashtag_user = _user("hashtag_user")
        removed_user = _user("removed_user")
        db.session.add(topic)
        db.session.flush()

        _explicit_post(explicit_user, topic, "Explicit Python")
        hashtag_post = Tweet(content="#Python", user_id=hashtag_user.id)
        removed_post = Tweet(content="Removed Python", user_id=removed_user.id, is_removed=True)
        db.session.add_all([hashtag_post, removed_post])
        db.session.flush()
        db.session.add_all(
            [
                TweetTopic(tweet_id=hashtag_post.id, topic_id=topic.id, source="hashtag"),
                TweetTopic(tweet_id=removed_post.id, topic_id=topic.id, source="explicit"),
            ]
        )
        db.session.commit()

        _, contributors = topic_contributors("python")

        assert [item["user"].username for item in contributors] == ["explicit_user"]


def test_topic_discovery_route_renders_rule_evidence_and_profile_links(client, app):
    with app.app_context():
        topic = Topic(name="RV Towing", slug="rv-towing")
        author = _user("tow_author")
        viewer = _user("viewer")
        db.session.add(topic)
        db.session.flush()
        tweet = _explicit_post(author, topic, "Towing setup")
        _recognize(viewer, tweet, "context")
        db.session.commit()
        viewer_id = viewer.id

    _login(client, viewer_id)
    response = client.get("/topic/rv-towing")

    assert response.status_code == 200
    assert b"People contributing to RV Towing" in response.data
    assert b"Contributor ordering is visible and deterministic" in response.data
    assert b"Followers, impressions, paid plans, and verification never affect placement" in response.data
    assert b"tow_author" in response.data
    assert b"Emerging contributor" in response.data
    assert b"Useful context" in response.data
    assert b"/profile/tow_author" in response.data


def test_existing_topic_with_no_eligible_contributors_degrades_gracefully(client, app):
    with app.app_context():
        topic = Topic(name="Quiet Topic", slug="quiet-topic")
        viewer = _user("viewer_empty")
        db.session.add(topic)
        db.session.commit()
        viewer_id = viewer.id

    _login(client, viewer_id)
    response = client.get("/topic/quiet-topic")

    assert response.status_code == 200
    assert b"No contributor history yet" in response.data


def test_unknown_topic_returns_404(client, app):
    with app.app_context():
        viewer = _user("viewer_404")
        db.session.commit()
        viewer_id = viewer.id

    _login(client, viewer_id)
    response = client.get("/topic/does-not-exist")

    assert response.status_code == 404
