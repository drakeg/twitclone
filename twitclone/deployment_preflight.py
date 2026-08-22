"""Production dependency checks used immediately before a release."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from alembic.config import Config as AlembicConfig
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text

from twitclone.media_storage import MediaNotFound


class DeploymentPreflightError(RuntimeError):
    """Raised when a production dependency is not ready for traffic."""


@dataclass(frozen=True)
class DeploymentPreflightResult:
    database: str
    migrations: str
    media: str


def _expected_migration_heads(migrations_directory: Path) -> set[str]:
    config = AlembicConfig()
    config.set_main_option("script_location", str(migrations_directory))
    return set(ScriptDirectory.from_config(config).get_heads())


def _current_migration_heads(connection) -> set[str]:
    return set(MigrationContext.configure(connection).get_current_heads())


def run_deployment_preflight(*, database_session, media_storage, migrations_directory):
    """Verify database access, migration state, and private media read/write."""
    try:
        database_session.execute(text("SELECT 1"))
        connection = database_session.connection()
    except Exception as exc:
        try:
            database_session.rollback()
        except Exception:
            pass
        raise DeploymentPreflightError("Database connectivity check failed.") from exc

    migrations_directory = Path(migrations_directory)
    try:
        expected_heads = _expected_migration_heads(migrations_directory)
        current_heads = _current_migration_heads(connection)
    except Exception as exc:
        raise DeploymentPreflightError(
            "Database migration state could not be inspected."
        ) from exc
    if current_heads != expected_heads:
        raise DeploymentPreflightError(
            "Database migration check failed: "
            f"expected {sorted(expected_heads)}, found {sorted(current_heads)}."
        )

    probe_name = f".ripple-preflight-{uuid4().hex}.bin"
    probe_content = uuid4().bytes
    written = False
    try:
        media_storage.put(
            probe_name,
            probe_content,
            content_type="application/octet-stream",
        )
        written = True
        stored = media_storage.get(probe_name)
        if stored.content != probe_content:
            raise DeploymentPreflightError(
                "Media storage verification returned different content."
            )
    except DeploymentPreflightError:
        raise
    except Exception as exc:
        raise DeploymentPreflightError("Media storage read/write check failed.") from exc
    finally:
        if written:
            try:
                media_storage.delete(probe_name)
            except Exception as exc:
                raise DeploymentPreflightError(
                    "Media storage probe cleanup failed."
                ) from exc

    try:
        media_storage.get(probe_name)
    except MediaNotFound:
        pass
    except Exception as exc:
        raise DeploymentPreflightError(
            "Media storage probe cleanup verification failed."
        ) from exc
    else:
        raise DeploymentPreflightError(
            "Media storage probe still exists after cleanup."
        )

    return DeploymentPreflightResult(
        database="connected",
        migrations=",".join(sorted(current_heads)),
        media="write/read/delete verified",
    )


__all__ = [
    "DeploymentPreflightError",
    "DeploymentPreflightResult",
    "run_deployment_preflight",
]
