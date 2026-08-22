# ADR-0039: Production deployment preflight

- Status: Accepted
- Date: 2026-08-21
- Sprint: 6
- Story: 6.7

## Context

Ripple validates required production settings during startup and exposes a
database readiness endpoint. Those checks do not prove that the deployed schema
matches the release or that the application identity can write, read, and clean
up private media. Operators otherwise have to combine several informal checks
at the highest-risk point in a release.

## Decision

- Provide `flask --app application deployment-preflight` as a production-only,
  one-shot release check.
- Verify database connectivity and require the database's Alembic heads to
  exactly match the migration heads shipped in the release image.
- Verify private media write, read, content equality, delete, and deletion using
  a unique disposable object under the configured application prefix.
- Return a nonzero exit code with a stage-specific message on any failure,
  without logging credentials or connection details.
- Run the check after migrations and before public traffic is enabled.

## Consequences

- A release can be blocked before traffic when its database or media access is
  incomplete or points at an unexpected schema.
- The application identity needs delete permission in addition to ordinary
  media read/write access, matching Ripple's existing cleanup behavior.
- Preflight is intentionally not a substitute for backups, restore rehearsals,
  health checks, or user-facing smoke tests.
- Local Compose and `docker compose run --rm test` remain unchanged.
