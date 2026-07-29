"""Regression tests for package-owned utility behavior."""

from __future__ import annotations

import hashlib

from PIL import Image

import app as legacy_app
from twitclone.extensions import db
from twitclone.models import Tweet, User
from twitclone.utils import (
    get_newest_users,
    get_trending_hashtags,
    gravatar,
    make_clickable_links,
    resize_image,
)


def test_gravatar_preserves_existing_url_format():
    email = "Example@Email.com"
    digest = hashlib.md5(email.lower().encode("utf-8")).hexdigest()

    assert gravatar(email) == (
        f"https://www.gravatar.com/avatar/{digest}?s=100&d=identicon&r=g"
    )
    assert gravatar(email, size=48, default="retro", rating="pg") == (
        f"https://www.gravatar.com/avatar/{digest}?s=48&d=retro&r=pg"
    )


def test_make_clickable_links_preserves_existing_markup():
    assert make_clickable_links("Hello @mallard from #UpstateNY") == (
        'Hello <a href="/profile/mallard">@mallard</a> from '
        '<a href="/hashtag/UpstateNY">#UpstateNY</a>'
    )


def test_resize_image_preserves_aspect_ratio_and_default_bounds(tmp_path):
    source = tmp_path / "source.png"
    output = tmp_path / "output.png"
    Image.new("RGB", (400, 100)).save(source)

    resize_image(source, output)

    with Image.open(output) as resized:
        assert resized.size == (200, 50)


def test_newest_users_and_trending_hashtags_preserve_query_behavior(app):
    with app.app_context():
        first = User(username="first", email="first@example.com", password="hash")
        second = User(username="second", email="second@example.com", password="hash")
        third = User(username="third", email="third@example.com", password="hash")
        db.session.add_all([first, second, third])
        db.session.flush()
        db.session.add_all(
            [
                Tweet(content="#rv #travel", user_id=first.id),
                Tweet(content="#rv #camping", user_id=second.id),
                Tweet(content="#rv #travel", user_id=third.id),
            ]
        )
        db.session.commit()

        assert [user.username for user in get_newest_users(limit=2)] == [
            "third",
            "second",
        ]
        assert get_trending_hashtags() == ["rv", "travel", "camping"]


def test_supported_runtime_binds_legacy_names_to_package_utilities():
    assert legacy_app.gravatar is gravatar
    assert legacy_app.get_newest_users is get_newest_users
    assert legacy_app.get_trending_hashtags is get_trending_hashtags
    assert legacy_app.resize_image is resize_image
    assert legacy_app.make_clickable_links is make_clickable_links
