# Application configuration

TwitClone configuration is supplied through environment variables and loaded by `config.py`.

## Supported entry point

Run the application through `application.py` so the centralized configuration is applied:

```bash
python application.py
```

For Gunicorn, use `application:application`. See
[`production-serving.md`](production-serving.md) for the supported command and
process boundaries.

The original `app.py` remains the legacy monolith during the stabilization sprints. New operational instructions should use the configured entry point above.

## Local setup

1. Copy `.env.example` to a local `.env` or export the variables through your shell or process manager.
2. Replace the placeholder `SECRET_KEY` with a random value.
3. Install development dependencies:

   ```bash
   python -m pip install -r requirements-dev.txt
   ```

4. Run configuration tests:

   ```bash
   python -m pytest tests/test_config.py
   ```

Docker Compose automatically reads the repository `.env` file for variable interpolation, and `compose.yaml` passes the documented application settings into the migrate, web, and worker containers with safe local defaults. Copy `.env.example` to `.env` when using Compose. Direct `python application.py` execution still does not parse `.env` itself; export variables through the shell or a development tool when running outside Compose.

## Variables

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `RIPPLE_BIND_HOST` | Compose only | `0.0.0.0` | Host interface used for the published local container port. |
| `RIPPLE_PORT` | Compose only | `8000` | Host port published to Ripple's fixed container port 8000. |
| `TWITCLONE_ENV` | No | `development` | Selects development, testing, or production behavior. |
| `SECRET_KEY` | Yes | None | Signs sessions and CSRF tokens. Startup fails in every environment when absent. |
| `DATABASE_URL` | Production | Local SQLite database | SQLAlchemy database connection URL. Production requires PostgreSQL. |
| `UPLOAD_FOLDER` | No | `static/uploads` | Development filesystem location for uploaded post images. Production must use the durable media adapter defined by the operations runbook. |
| `MEDIA_STORAGE_BACKEND` | No | `filesystem` | `filesystem` for local development and `s3` for production. |
| `MEDIA_S3_BUCKET` | S3 backend | None | Private S3-compatible bucket name. |
| `MEDIA_S3_REGION` | S3 backend | None | Bucket region used by the S3 client. |
| `MEDIA_S3_ENDPOINT_URL` | No | AWS default | Optional endpoint for S3-compatible providers. |
| `MEDIA_S3_PREFIX` | No | `media` | Object-key prefix within the bucket. |
| `SCHEDULER_ENABLED` | No | `true` | Enables or disables scheduled-post processing. |
| `SCHEDULER_INTERVAL_SECONDS` | No | `60` | Scheduler polling interval; must be at least one second. |
| `PORT` | No | `8000` | Port used by the local `application.py` runner. |
| `STRIPE_API_VERSION` | No | `2026-03-25.dahlia` | Stripe API contract used for outbound billing requests; pin independently from the SDK major and change only with a reviewed API migration. |

## Environment guidance

### Development

Set a unique local `SECRET_KEY`; the application intentionally has no built-in fallback. Compose supplies a local development default only when the variable is omitted, while direct host execution requires you to export one.

### Testing

Set `TWITCLONE_ENV=testing`, use an isolated database such as `sqlite:///:memory:`, and set `SCHEDULER_ENABLED=false`.

### Production

Set `TWITCLONE_ENV=production` and provide a strong `SECRET_KEY`. The application raises a clear startup error if the production secret is missing.

Production processes must supply a PostgreSQL URL and an upload location
appropriate to the deployment platform. `postgres://` and `postgresql://` URLs
are normalized to the supported Psycopg 3 SQLAlchemy driver. SQLite production
startup is rejected. See [`database.md`](database.md) for the migration and
release procedure and [`operations.md`](operations.md) for the durable-media,
backup, restore, and rollback contract. Production requires the S3 backend, a
bucket, and a region. Credentials use Boto3's standard credential chain and
must be injected by the platform rather than stored in application settings.
Use the verified `flask --app application migrate-media-to-s3` procedure in the
operations runbook before switching an existing deployment to S3-backed media.

## Security notes

- Never commit a real `.env` file or production secret.
- Rotate any secret that has been exposed in source control or logs.
- Use the hosting platform's secret manager or environment configuration for production values.
- Do not run production using Flask's development server.


## Stripe API compatibility

Ripple pins `STRIPE_API_VERSION` separately from the `stripe-python` package version. A major SDK upgrade may change the SDK default API version; upgrading the library alone must not silently migrate Ripple's Checkout or Billing Portal request contract. Review Stripe's API changelog and update `STRIPE_API_VERSION` only as a separate, tested migration. Webhook endpoint versioning remains configured in Stripe and must be reviewed independently.
