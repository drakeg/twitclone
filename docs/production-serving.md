# Production WSGI serving

Ripple's supported WSGI entry point is `application:application`. The container and Docker Compose web service use Gunicorn instead of Flask's development server:

```bash
gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 4 --timeout 30 application:application
```

The single worker is intentional for the current SQLite-based local Compose setup. Threads allow concurrent request handling without creating multiple application processes that contend for the local database. Do not increase the local worker count while using SQLite. Production uses PostgreSQL, but concurrency must still be sized and load-tested for the selected hosting plan.

## Process boundaries

The web process serves HTTP requests only. It must not apply database migrations or run scheduled-post processing during startup.

Local Compose preserves those boundaries with three application services:

- `migrate` applies migrations once and must finish successfully first.
- `web` runs Gunicorn and starts only after migration succeeds.
- `worker` publishes scheduled posts and starts only after migration succeeds.

Run the complete local stack with:

```bash
docker compose up --build
```

Sprint 8 adds a separate `compose.production.yaml` release contract without changing this local workflow. Production adds an explicit `preflight` one-shot service and a Caddy reverse-proxy/TLS service while preserving the same migration/web/worker separation. See [`container-deployment.md`](container-deployment.md).

## Deployment responsibilities

Before exposing Ripple publicly, the hosting environment must also provide:

- TLS termination and trusted proxy configuration.
- A strong `SECRET_KEY` supplied outside source control.
- PostgreSQL configured and migrated using [`database.md`](database.md).
- Private durable S3-backed media storage.
- External monitoring, backups, and rollback procedures. The application health and structured-log contracts are documented in [`observability.md`](observability.md); recovery procedures and launch gates are documented in [`operations.md`](operations.md).
- Exactly one scheduled-post worker until database-level job claiming exists.

Gunicorn handles termination signals and allows in-flight requests up to the configured 30-second timeout. The deployment platform should stop accepting new traffic before terminating the web container and allow enough shutdown time for active requests to finish.

The Docker image's default command is the same Gunicorn command used by Compose. Database migration remains an explicit release or one-shot task rather than a side effect of starting each web replica. After that task succeeds, run `flask --app application deployment-preflight` using the release image before enabling public traffic; the full sequence is in [`container-deployment.md`](container-deployment.md) and [`operations.md`](operations.md).

## AWS readiness without AWS spend

The production container contract is intentionally provider-light. It can be prepared and validated while Ripple continues to run only in local containers. A future EC2 host is expected to provide Docker/Compose, the host-only production environment file, network access to private RDS, and an IAM instance role for S3. Neither this document nor the production Compose file provisions AWS resources.
