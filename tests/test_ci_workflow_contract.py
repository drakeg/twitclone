"""Regression coverage for GitHub Actions workflow scheduling.

Unquoted SQLite URLs ending in a colon caused the CI workflow to fail during
GitHub's workflow parsing, before any job could be created.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_quotes_sqlite_url_and_retains_all_validation_jobs():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert 'DATABASE_URL: "sqlite:///:memory:"' in workflow
    assert "DATABASE_URL: sqlite:///:memory:" not in workflow
    assert "  test:\n" in workflow
    assert "  release-image:\n" in workflow
    assert "  terraform:\n" in workflow
