"""Regression coverage for local demo content seeding."""

from twitclone.demo import DEMO_PASSWORD, DEMO_USERS, seed_demo_content
from twitclone.extensions import bcrypt
from twitclone.models import Quote, Retweet, Tweet, User


def test_seed_demo_content_creates_sample_users_and_social_activity(app):
    with app.app_context():
        result = seed_demo_content(seed=7)

        assert result["users"] == len(DEMO_USERS)
        assert result["posts"] >= len(DEMO_USERS)
        assert Retweet.query.count() > 0
        assert Quote.query.count() > 0

        users = User.query.filter(User.email.like("%@example.test")).all()
        assert len(users) == len(DEMO_USERS)
        assert all(bcrypt.check_password_hash(user.password, DEMO_PASSWORD) for user in users)

        contents = [tweet.content for tweet in Tweet.query.all()]
        assert any("#" in content for content in contents)
        assert any("@" in content for content in contents)


def test_seed_demo_content_is_idempotent(app):
    with app.app_context():
        seed_demo_content(seed=11)
        counts_before = (
            User.query.count(),
            Tweet.query.count(),
            Retweet.query.count(),
            Quote.query.count(),
        )

        second = seed_demo_content(seed=11)
        counts_after = (
            User.query.count(),
            Tweet.query.count(),
            Retweet.query.count(),
            Quote.query.count(),
        )

        assert second["users"] == 0
        assert second["posts"] == 0
        assert counts_after == counts_before


def test_anonymous_home_renders_seeded_public_posts(client, app):
    with app.app_context():
        seed_demo_content(seed=13)

    response = client.get("/")

    assert response.status_code == 200
    assert b"Welcome to Ripple" in response.data
    assert any(username.encode() in response.data for username, _, _ in DEMO_USERS)
