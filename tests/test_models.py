"""Regression tests for the package-owned SQLAlchemy models."""

import inspect


EXPECTED_COLUMNS = {
    "follows": {"follower_id", "followed_id"},
    "user": {"id", "username", "email", "password", "bio"},
    "tweet": {"id", "content", "timestamp", "user_id", "image", "scheduled_at"},
    "retweet": {"id", "user_id", "tweet_id", "timestamp"},
    "quote": {"id", "user_id", "tweet_id", "content", "timestamp"},
    "direct_message": {"id", "content", "sender_id", "receiver_id", "timestamp"},
    "notification": {"id", "user_id", "message", "timestamp", "read"},
    "bookmark": {"id", "user_id", "tweet_id", "timestamp"},
    "poll": {
        "id",
        "question",
        "created_at",
        "duration_days",
        "duration_hours",
        "duration_minutes",
        "user_id",
    },
    "poll_option": {"id", "option_text", "poll_id", "votes"},
    "poll_vote": {"id", "poll_id", "user_id", "option_id"},
}


def test_legacy_module_exports_package_model_classes():
    import app as legacy_app
    import twitclone.models as models

    for model_name in models.__all__:
        assert getattr(legacy_app, model_name) is getattr(models, model_name)


def test_model_metadata_preserves_table_and_column_inventory():
    from twitclone.extensions import db

    assert set(db.metadata.tables) == set(EXPECTED_COLUMNS)

    for table_name, expected_columns in EXPECTED_COLUMNS.items():
        table = db.metadata.tables[table_name]
        assert set(table.columns.keys()) == expected_columns


def test_relationships_remain_registered():
    from twitclone.models import Bookmark, DirectMessage, Poll, Quote, Retweet, Tweet, User

    assert {relationship.key for relationship in User.__mapper__.relationships} == {
        "followed",
        "notifications",
        "bookmarks",
        "followers",
        "tweets",
        "retweets",
        "quotes",
        "sent_messages",
        "received_messages",
        "polls",
        "bookmark_relationships",
    }
    assert {relationship.key for relationship in Tweet.__mapper__.relationships} == {
        "user",
        "retweets",
        "quotes",
        "bookmarked_tweets",
    }
    assert {relationship.key for relationship in Retweet.__mapper__.relationships} == {"user", "tweet"}
    assert {relationship.key for relationship in Quote.__mapper__.relationships} == {"user", "tweet"}
    assert {relationship.key for relationship in DirectMessage.__mapper__.relationships} == {"sender", "receiver"}
    assert {relationship.key for relationship in Bookmark.__mapper__.relationships} == {"user", "tweet"}
    assert {relationship.key for relationship in Poll.__mapper__.relationships} == {"user", "options"}


def test_login_loader_returns_package_user(app):
    import app as legacy_app
    from twitclone.extensions import db
    from twitclone.models import User

    user = User(username="model-test", email="model-test@example.com", password="not-used")
    with app.app_context():
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        loaded_user = legacy_app.load_user(str(user_id))

        assert loaded_user is not None
        assert isinstance(loaded_user, User)
        assert loaded_user.id == user_id


def test_legacy_module_no_longer_declares_models():
    import app as legacy_app

    source = inspect.getsource(legacy_app)
    for model_name in (
        "Follows",
        "User",
        "Tweet",
        "Retweet",
        "Quote",
        "DirectMessage",
        "Notification",
        "Bookmark",
        "Poll",
        "PollOption",
        "PollVote",
    ):
        assert f"class {model_name}(" not in source
