import pytest
from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory
from sqlalchemy import text

from twitclone.deployment_preflight import (
    DeploymentPreflightError,
    run_deployment_preflight,
)
from twitclone.extensions import db
from twitclone.media_storage import MediaNotFound, StoredMedia


@pytest.fixture(autouse=True)
def clear_migration_version_table(app):
    with app.app_context():
        db.session.execute(text("DROP TABLE IF EXISTS alembic_version"))
        db.session.commit()
    yield
    with app.app_context():
        db.session.execute(text("DROP TABLE IF EXISTS alembic_version"))
        db.session.commit()


class MemoryStorage:
    def __init__(self, *, corrupt_reads=False, retain_deletes=False):
        self.objects = {}
        self.corrupt_reads = corrupt_reads
        self.retain_deletes = retain_deletes

    def put(self, name, content, *, content_type=None):
        self.objects[name] = bytes(content)

    def get(self, name):
        try:
            content = self.objects[name]
        except KeyError as exc:
            raise MediaNotFound(name) from exc
        if self.corrupt_reads:
            content = b"different"
        return StoredMedia(content, "application/octet-stream")

    def delete(self, name):
        if not self.retain_deletes:
            self.objects.pop(name, None)


def migration_head():
    config = AlembicConfig()
    config.set_main_option("script_location", "migrations")
    return ScriptDirectory.from_config(config).get_current_head()


def mark_database_current():
    db.session.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
    db.session.execute(
        text("INSERT INTO alembic_version (version_num) VALUES (:head)"),
        {"head": migration_head()},
    )
    db.session.commit()


def test_deployment_preflight_verifies_all_dependencies_and_cleans_probe(app):
    storage = MemoryStorage()
    with app.app_context():
        mark_database_current()

        result = run_deployment_preflight(
            database_session=db.session,
            media_storage=storage,
            migrations_directory="migrations",
        )

    assert result.database == "connected"
    assert result.migrations == migration_head()
    assert result.media == "write/read/delete verified"
    assert storage.objects == {}


def test_deployment_preflight_rejects_outdated_database(app):
    with app.app_context(), pytest.raises(
        DeploymentPreflightError, match="Database migration check failed"
    ):
        run_deployment_preflight(
            database_session=db.session,
            media_storage=MemoryStorage(),
            migrations_directory="migrations",
        )


def test_deployment_preflight_rejects_missing_migration_directory(app, tmp_path):
    with app.app_context(), pytest.raises(
        DeploymentPreflightError, match="migration state could not be inspected"
    ):
        run_deployment_preflight(
            database_session=db.session,
            media_storage=MemoryStorage(),
            migrations_directory=tmp_path / "missing",
        )


def test_deployment_preflight_rejects_corrupt_media_read_and_cleans_probe(app):
    storage = MemoryStorage(corrupt_reads=True)
    with app.app_context():
        mark_database_current()
        with pytest.raises(DeploymentPreflightError, match="different content"):
            run_deployment_preflight(
                database_session=db.session,
                media_storage=storage,
                migrations_directory="migrations",
            )

    assert storage.objects == {}


def test_deployment_preflight_rejects_failed_media_cleanup(app):
    storage = MemoryStorage(retain_deletes=True)
    with app.app_context():
        mark_database_current()
        with pytest.raises(DeploymentPreflightError, match="still exists"):
            run_deployment_preflight(
                database_session=db.session,
                media_storage=storage,
                migrations_directory="migrations",
            )


def test_deployment_preflight_cli_requires_production(app):
    previous_environment = app.config.get("ENVIRONMENT")
    app.config["ENVIRONMENT"] = "testing"
    try:
        result = app.test_cli_runner().invoke(args=["deployment-preflight"])
    finally:
        app.config["ENVIRONMENT"] = previous_environment

    assert result.exit_code != 0
    assert "Set TWITCLONE_ENV=production" in result.output


def test_deployment_preflight_cli_reports_success(app):
    storage = MemoryStorage()
    previous_environment = app.config.get("ENVIRONMENT")
    previous_storage = app.extensions.get("media_storage")
    app.config["ENVIRONMENT"] = "production"
    app.extensions["media_storage"] = storage
    try:
        with app.app_context():
            mark_database_current()
        result = app.test_cli_runner().invoke(args=["deployment-preflight"])
    finally:
        app.config["ENVIRONMENT"] = previous_environment
        app.extensions["media_storage"] = previous_storage

    assert result.exit_code == 0, (result.output, result.exception)
    assert "Database: connected" in result.output
    assert f"Migrations: current ({migration_head()})" in result.output
    assert "Media: write/read/delete verified" in result.output
    assert result.output.endswith("Deployment preflight passed.\n")
    assert storage.objects == {}
