# ADR-0030: Production WSGI serving

- Status: Accepted
- Date: 2026-08-15
- Sprint: 6
- Story: 6.1

## Context

The image and Compose web service started Flask's development server. The image
also applied migrations in its default web startup command. That couples a
one-time database operation to every web replica and does not provide a
production-capable HTTP process.

## Decision

- Pin Gunicorn as an application runtime dependency.
- Serve the supported `application:application` WSGI entry point.
- Use one worker and four threads for the SQLite-based local Compose stack.
- Keep migrations in the one-shot `migrate` service and scheduled publishing in
  the dedicated `worker` service.
- Give the image and Compose web service the same explicit Gunicorn command.
- Defer multi-process sizing until a production database is selected.

## Consequences

- `docker compose up --build` exercises the production-style WSGI boundary.
- Web restarts cannot implicitly run migrations or scheduled jobs.
- The current concurrency setting is deliberately conservative and is not a
  final production capacity recommendation.
- Public deployment still depends on the remaining Sprint 6 operational work.

## Guardrails

- Flask's development server must not be used by the container web service.
- Web process startup must not mutate the schema.
- Worker count must remain one while the Compose database is SQLite.
