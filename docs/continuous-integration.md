# Continuous Integration and Testing

## Purpose

TwitClone uses pytest and GitHub Actions to validate the minimum safe development baseline on every pull request and every push to `main`.

The initial suite is intentionally small. It confirms that the application can be installed, configured, migrated, imported, and served without touching a developer database or starting the background scheduler.

## Supported Runtime

CI runs on Python 3.12, matching `.python-version`.

## Local Setup

Create and activate a virtual environment, then install development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

On Windows PowerShell, activate with:

```powershell
.venv\Scripts\Activate.ps1
```

## Run the Full Validation Set

Run the same logical checks used by CI:

```bash
python scripts/verify_dependencies.py
python scripts/verify_migrations.py
python -m pytest --strict-markers --maxfail=1
```

The pytest command alone is:

```bash
python -m pytest
```

## Test Isolation

The test environment sets:

- `TWITCLONE_ENV=testing`
- a test-only secret
- `DATABASE_URL=sqlite:///:memory:`
- a temporary upload path
- `SCHEDULER_ENABLED=false`

The application tables are created in memory before each smoke test and removed afterward. Tests must never use the normal local SQLite database.

## Current Smoke Coverage

The baseline tests verify:

- testing configuration is active
- the database uses in-memory SQLite
- the background scheduler is stopped
- the public homepage returns HTTP 200
- the login page returns HTTP 200
- existing configuration validation tests continue to pass

This is not comprehensive feature coverage. Authentication, posting, follows, messaging, polls, uploads, and scheduling need focused tests in later sprints.

## GitHub Actions

Workflow file:

```text
.github/workflows/ci.yml
```

Triggers:

- every pull request
- every push to `main`

The workflow performs:

1. repository checkout
2. Python 3.12 setup
3. dependency installation
4. dependency import verification
5. migration verification against disposable SQLite
6. pytest execution

The workflow uses read-only repository permissions and does not deploy infrastructure or access AWS.

## Troubleshooting

### Dependency installation fails

Reproduce locally in a new virtual environment. Do not solve resolver failures by removing merged security pins without reviewing the originating advisory.

### Dependency verification fails

The verifier reports the import that failed. Confirm the relevant direct dependency remains in `requirements.txt` and is compatible with Python 3.12.

### Migration verification fails

Run:

```bash
python scripts/verify_migrations.py
```

Review the first failing Flask-Migrate or Alembic command. Do not repair an existing personal database while diagnosing the clean-database workflow.

### Smoke test accesses a local database

Confirm `tests/conftest.py` sets `DATABASE_URL` before importing `application`. Database configuration must be established before Flask-SQLAlchemy first creates its engine.

### Scheduler remains active

Confirm `SCHEDULER_ENABLED=false` is present before application import and that the test fixture shuts down any legacy scheduler instance. This is transitional until the application-factory refactor prevents scheduler startup at import time.

### A bot PR changes the workflow

Treat CI workflow changes as production-impacting. Review action versions, permissions, event triggers, and any newly introduced secrets before merging.

## Branch Protection Recommendation

After this workflow passes reliably on `main`, configure branch protection to require the `Python 3.12 validation` job before merging. Branch protection is a repository setting and is not changed by this PR.

## AWS Relationship

This CI workflow has no AWS cost. Future Terraform validation can be added without AWS credentials by running `terraform fmt -check` and `terraform validate`. Deployment workflows that can create billable resources must remain separate and require explicit approval.
