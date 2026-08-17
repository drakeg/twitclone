from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_avoids_deprecated_datetime_utcnow():
    runtime_files = (
        ROOT / "twitclone/models.py",
        ROOT / "twitclone/timeline/routes.py",
    )

    for path in runtime_files:
        assert "datetime.utcnow" not in path.read_text(encoding="utf-8")
