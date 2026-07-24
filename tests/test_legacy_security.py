"""Security regression tests for the legacy application module."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_predictable_flask_secrets_are_absent_from_active_source():
    """Known placeholder signing keys must never return to active source."""

    active_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            REPOSITORY_ROOT / "app.py",
            REPOSITORY_ROOT / "config.py",
            REPOSITORY_ROOT / "application.py",
            REPOSITORY_ROOT / "twitclone" / "__init__.py",
        )
    )

    assert "your_secret_key" not in active_source
    assert "development-only-change-me" not in active_source


def test_direct_legacy_import_requires_external_secret_key():
    """Importing app.py directly must fail clearly without SECRET_KEY."""

    environment = os.environ.copy()
    environment.pop("SECRET_KEY", None)
    environment.update(
        TWITCLONE_ENV="development",
        DATABASE_URL="sqlite:///:memory:",
        SCHEDULER_ENABLED="false",
    )

    result = subprocess.run(
        [sys.executable, "-c", "import app"],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "SECRET_KEY is required" in output


def test_scheduler_remains_stopped_when_disabled():
    """The test environment must not start the legacy background scheduler."""

    from app import scheduler

    assert scheduler.running is False
