from pathlib import Path

from twitclone.media_migration import migrate_media_directory
from twitclone.media_storage import MediaNotFound, StoredMedia


class MemoryStorage:
    def __init__(self, objects=None):
        self.objects = dict(objects or {})

    def get(self, name):
        try:
            return StoredMedia(self.objects[name], "application/octet-stream")
        except KeyError as exc:
            raise MediaNotFound(name) from exc

    def put(self, name, content, *, content_type=None):
        self.objects[name] = content


def test_media_migration_copies_verifies_and_is_repeatable(tmp_path):
    (tmp_path / "thumb_one.png").write_bytes(b"one")
    (tmp_path / "original_one.png").write_bytes(b"original")
    storage = MemoryStorage()

    first = migrate_media_directory(tmp_path, storage)
    second = migrate_media_directory(tmp_path, storage)

    assert first.discovered == 2
    assert first.copied == 2
    assert first.bytes_copied == 11
    assert second.copied == 0
    assert second.unchanged == 2


def test_media_migration_dry_run_does_not_write(tmp_path):
    (tmp_path / "banner_one.png").write_bytes(b"banner")
    storage = MemoryStorage()

    result = migrate_media_directory(tmp_path, storage, dry_run=True)

    assert result.copied == 1
    assert result.bytes_copied == 6
    assert storage.objects == {}


def test_media_migration_refuses_conflicts_without_explicit_overwrite(tmp_path):
    (tmp_path / "thumb_one.png").write_bytes(b"new")
    storage = MemoryStorage({"thumb_one.png": b"old"})

    refused = migrate_media_directory(tmp_path, storage)
    replaced = migrate_media_directory(tmp_path, storage, overwrite=True)

    assert refused.conflicts == 1
    assert storage.objects["thumb_one.png"] == b"new"
    assert replaced.copied == 1


def test_media_migration_ignores_hidden_files_directories_and_symlinks(tmp_path):
    (tmp_path / ".metadata").write_bytes(b"hidden")
    (tmp_path / "nested").mkdir()
    target = tmp_path / "thumb_one.png"
    target.write_bytes(b"one")
    (tmp_path / "linked.png").symlink_to(target)

    result = migrate_media_directory(tmp_path, MemoryStorage())

    assert result.discovered == 1


def test_media_migration_requires_existing_source_directory(tmp_path):
    missing = tmp_path / "missing"
    try:
        migrate_media_directory(missing, MemoryStorage())
    except ValueError as exc:
        assert str(missing) in str(exc)
    else:
        raise AssertionError("missing source should fail")


def test_media_migration_cli_reports_a_dry_run(app, tmp_path):
    (tmp_path / "thumb_one.png").write_bytes(b"one")
    storage = MemoryStorage()
    previous_backend = app.config.get("MEDIA_STORAGE_BACKEND")
    previous_storage = app.extensions.get("media_storage")
    app.config["MEDIA_STORAGE_BACKEND"] = "s3"
    app.extensions["media_storage"] = storage

    try:
        result = app.test_cli_runner().invoke(
            args=["migrate-media-to-s3", "--source", str(tmp_path), "--dry-run"]
        )
    finally:
        app.config["MEDIA_STORAGE_BACKEND"] = previous_backend
        app.extensions["media_storage"] = previous_storage

    assert result.exit_code == 0
    assert "Media migration plan: 1 discovered, 1 copied" in result.output
    assert storage.objects == {}


def test_media_migration_cli_requires_s3_backend(app, tmp_path):
    previous_backend = app.config.get("MEDIA_STORAGE_BACKEND")
    app.config["MEDIA_STORAGE_BACKEND"] = "filesystem"

    try:
        result = app.test_cli_runner().invoke(
            args=["migrate-media-to-s3", "--source", str(tmp_path)]
        )
    finally:
        app.config["MEDIA_STORAGE_BACKEND"] = previous_backend

    assert result.exit_code != 0
    assert "Set MEDIA_STORAGE_BACKEND=s3" in result.output
