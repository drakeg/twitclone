"""Apply migrations to an isolated SQLite database and verify expected tables."""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_COLUMNS = {
    "space": {"archived_at", "archived_by_id"},
}

EXPECTED_TABLES = {
    "alembic_version",
    "bookmark",
    "direct_message",
    "follows",
    "notification",
    "poll",
    "poll_option",
    "poll_vote",
    "quote",
    "retweet",
    "space_invitation",
    "space_membership_action",
    "tweet",
    "user",
}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="twitclone-migration-") as temp_dir:
        database_path = Path(temp_dir) / "migration-test.db"
        env = os.environ.copy()
        env.update(
            {
                "APP_ENV": "testing",
                "DATABASE_URL": f"sqlite:///{database_path.as_posix()}",
                "SECRET_KEY": "migration-verification-only",
                "SCHEDULER_ENABLED": "false",
            }
        )
        result = subprocess.run(
            [sys.executable, "-m", "flask", "--app", "application", "db", "upgrade"],
            cwd=repo_root,
            env=env,
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            return result.returncode

        with sqlite3.connect(database_path) as connection:
            rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        actual_tables = {row[0] for row in rows}
        missing = EXPECTED_TABLES - actual_tables
        if missing:
            print(f"Missing expected tables: {sorted(missing)}", file=sys.stderr)
            return 1

        with sqlite3.connect(database_path) as connection:
            for table_name, expected_columns in EXPECTED_COLUMNS.items():
                columns = {
                    row[1]
                    for row in connection.execute(
                        f"PRAGMA table_info({table_name})"
                    ).fetchall()
                }
                missing_columns = expected_columns - columns
                if missing_columns:
                    print(
                        f"Missing expected columns on {table_name}: {sorted(missing_columns)}",
                        file=sys.stderr,
                    )
                    return 1

        print("Migration verification passed.")
        print(f"Created tables: {', '.join(sorted(actual_tables))}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
