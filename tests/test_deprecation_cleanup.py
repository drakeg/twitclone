"""Regression guards for APIs deprecated by current Python and SQLAlchemy."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_routes_avoid_deprecated_primary_key_query_getters():
    route_files = [
        ROOT / "twitclone/bookmarks/routes.py",
        ROOT / "twitclone/polls/routes.py",
        ROOT / "twitclone/profiles/routes.py",
        ROOT / "twitclone/timeline/routes.py",
    ]

    for path in route_files:
        source = path.read_text(encoding="utf-8")
        assert ".query.get(" not in source
        assert ".query.get_or_404(" not in source


def test_updated_runtime_and_tests_avoid_datetime_utcnow():
    paths = [
        ROOT / "twitclone/polls/routes.py",
        ROOT / "tests/test_notifications.py",
        ROOT / "tests/test_polls.py",
    ]

    for path in paths:
        assert "datetime.utcnow(" not in path.read_text(encoding="utf-8")
