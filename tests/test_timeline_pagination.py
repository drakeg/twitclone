"""Timeline pagination tests."""

from datetime import datetime, timedelta

import pytest

from twitclone.extensions import db
from twitclone.models import Tweet, User
from twitclone.timeline.service import TIMELINE_PAGE_SIZE, paginate_timeline_posts


def seed_tweets(app, *, count, tied=False):
    fixed_time = datetime(2026, 8, 12, 12, 0, 0)
    with app.app_context():
        user = User(username="author", email="author@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        for index in range(count):
            timestamp = fixed_time if tied else fixed_time - timedelta(minutes=index)
            db.session.add(
                Tweet(content=f"timeline item {index:02d}", user_id=user.id, timestamp=timestamp)
            )
        db.session.commit()


def test_paginator_returns_bounded_pages_without_gaps_or_duplicates():
    posts = [{"id": identifier} for identifier in range(45)]

    first = paginate_timeline_posts(posts, page=1)
    second = paginate_timeline_posts(posts, page=2)
    third = paginate_timeline_posts(posts, page=3)

    assert TIMELINE_PAGE_SIZE == 20
    assert [len(first.items), len(second.items), len(third.items)] == [20, 20, 5]
    assert first.total_items == 45
    assert first.total_pages == 3
    assert first.has_previous is False
    assert first.next_page == 2
    assert second.previous_page == 1
    assert second.next_page == 3
    assert third.has_next is False
    assert [item["id"] for page in (first, second, third) for item in page.items] == list(
        range(45)
    )


@pytest.mark.parametrize(("requested", "expected"), [(-2, 1), (0, 1), (99, 3)])
def test_paginator_bounds_requested_page(requested, expected):
    page = paginate_timeline_posts(list(range(41)), page=requested)

    assert page.page == expected


def test_empty_timeline_has_one_empty_page():
    page = paginate_timeline_posts([], page=9)

    assert page.items == []
    assert page.page == 1
    assert page.total_pages == 1
    assert page.has_previous is False
    assert page.has_next is False


def test_invalid_page_size_is_rejected():
    with pytest.raises(ValueError, match="per_page must be at least 1"):
        paginate_timeline_posts([], page=1, per_page=0)


def test_index_paginates_using_deterministic_tie_order(client, app):
    seed_tweets(app, count=21, tied=True)

    first = client.get("/")
    second = client.get("/?page=2")

    assert first.status_code == 200
    assert second.status_code == 200
    assert b"Page 1 of 2" in first.data
    assert b'href="/?page=2"' in first.data
    assert b"Page 2 of 2" in second.data
    assert b'href="/?page=1"' in second.data
    for index in range(1, 21):
        assert f"timeline item {index:02d}".encode() in first.data
        assert f"timeline item {index:02d}".encode() not in second.data
    assert b"timeline item 00" not in first.data
    assert b"timeline item 00" in second.data


@pytest.mark.parametrize("path", ["/?page=invalid", "/?page=0", "/?page=-2"])
def test_invalid_and_non_positive_query_pages_normalize_to_first(client, app, path):
    seed_tweets(app, count=21)

    response = client.get(path)

    assert response.status_code == 200
    assert b"Page 1 of 2" in response.data
    assert b"timeline item 00" in response.data


def test_page_beyond_end_returns_last_page(client, app):
    seed_tweets(app, count=21)

    response = client.get("/?page=999")

    assert response.status_code == 200
    assert b"Page 2 of 2" in response.data
    assert b"timeline item 20" in response.data
