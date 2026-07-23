# Application configuration

TwitClone configuration is supplied through environment variables and loaded by `config.py`.

## Supported entry point

Run the application through `application.py` so the centralized configuration is applied:

```bash
python application.py
```

For a WSGI server, use `application:application`.

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

The project does not automatically parse `.env` yet. Export the variables or use a development tool that loads `.env` before starting Python. Automatic `.env` loading will be considered during dependency reconciliation rather than introducing an unreviewed dependency in this story.

## Variables

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `TWITCLONE_ENV` | No | `development` | Selects development, testing, or production behavior. |
| `SECRET_KEY` | Production only | Development-only fallback | Signs sessions and CSRF tokens. Production startup fails when absent. |
| `DATABASE_URL` | No | Local SQLite database | SQLAlchemy database connection URL. |
| `UPLOAD_FOLDER` | No | `static/uploads` | Location for uploaded post images. |
| `SCHEDULER_ENABLED` | No | `true` | Enables or disables scheduled-post processing. |
| `SCHEDULER_INTERVAL_SECONDS` | No | `60` | Scheduler polling interval; must be at least one second. |
| `PORT` | No | `8000` | Port used by the local `application.py` runner. |

## Environment guidance

### Development

Use a unique local secret where practical. The development fallback exists only to keep first-time setup simple and must never be treated as a deployment secret.

### Testing

Set `TWITCLONE_ENV=testing`, use an isolated database such as `sqlite:///:memory:`, and set `SCHEDULER_ENABLED=false`.

### Production

Set `TWITCLONE_ENV=production` and provide a strong `SECRET_KEY`. The application raises a clear startup error if the production secret is missing.

Production processes should also supply an explicit database URL and upload location appropriate to the deployment platform.

## Security notes

- Never commit a real `.env` file or production secret.
- Rotate any secret that has been exposed in source control or logs.
- Use the hosting platform's secret manager or environment configuration for production values.
- Do not run production using Flask's development server.
