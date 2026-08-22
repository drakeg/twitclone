# Production WSGI serving

TwitClone's supported WSGI entry point is `application:application`. The
container and Docker Compose web service use Gunicorn instead of Flask's
development server:

```bash
gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 4 --timeout 30 application:application
```

The single worker is intentional for the current SQLite-based local Compose setup.
Threads allow concurrent request handling without creating multiple application
processes that contend for the local database. Do not increase the local worker
count while using SQLite. Production uses PostgreSQL, but concurrency must still
be sized and load-tested for the selected hosting plan.

## Process boundaries

The web process serves HTTP requests only. It must not apply database migrations
or run scheduled-post processing during startup.

Compose preserves those boundaries with three services:

- `migrate` applies migrations once and must finish successfully first.
- `web` runs Gunicorn and starts only after migration succeeds.
- `worker` publishes scheduled posts and starts only after migration succeeds.

Run the complete local stack with:

```bash
docker compose up --build
```

## Deployment responsibilities

Before exposing TwitClone publicly, the hosting environment must also provide:

- TLS termination and trusted proxy configuration.
- A strong `SECRET_KEY` supplied by a secret manager.
- PostgreSQL configured and migrated using [`database.md`](database.md), plus
  durable uploaded-media storage.
- External monitoring, backups, and rollback procedures. The application health
  and structured-log contracts are documented in
  [`observability.md`](observability.md); recovery procedures and launch gates
  are documented in [`operations.md`](operations.md).
- Exactly one scheduled-post worker until database-level job claiming exists.

Gunicorn handles termination signals and allows in-flight requests up to the
configured 30-second timeout. The deployment platform should stop accepting new
traffic before terminating the web container and allow enough shutdown time for
active requests to finish.

The Docker image's default command is the same Gunicorn command used by Compose.
Database migration remains an explicit release or one-shot task rather than a
side effect of starting each web replica. After that task succeeds, run
`flask --app application deployment-preflight` using the release image before
enabling public traffic; the full sequence is in [`operations.md`](operations.md).
