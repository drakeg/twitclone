# ADR-0033: PostgreSQL for production

- Status: Accepted
- Date: 2026-08-16
- Sprint: 6
- Story: 6.3

## Context

SQLite keeps local development inexpensive and simple, but a single database
file is a poor boundary for concurrent production web and worker processes,
managed backups, network isolation, and independent application releases. The
previous documentation still proposed SQLite for the lowest-cost AWS plan.

## Decision

- Keep SQLite for local development, Compose, migration verification, and tests.
- Require managed PostgreSQL 18 for production.
- Use Psycopg 3 as SQLAlchemy's PostgreSQL driver.
- Normalize common provider URL schemes to `postgresql+psycopg://`.
- Reject production startup when the configured database is SQLite.
- Run migrations as an explicit release task before web and worker startup.
- Treat any SQLite-to-PostgreSQL data copy as a separate rehearsed operation.

## Consequences

- Production gains a durable, concurrent database boundary and provider-native
  backup options at additional monthly cost.
- Local `docker compose up --build` remains simple and unchanged.
- Production deployment cannot proceed until a PostgreSQL service and secret URL
  are provisioned.
- PostgreSQL migration compatibility must be validated in staging before release.

## Guardrails

- Database credentials must remain outside source, images, logs, and Terraform outputs.
- Web startup must not apply migrations implicitly.
- Exactly one scheduled worker remains the supported topology until job claiming
  is implemented.
- Production downgrades are never automatic.
