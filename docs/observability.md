# Health checks and structured logs

TwitClone exposes two unauthenticated operational endpoints:

| Endpoint | Purpose | Success | Failure |
| --- | --- | --- | --- |
| `/health/live` | Confirms the web process can answer HTTP requests | `200 {"status":"ok"}` | Process or network failure |
| `/health/ready` | Confirms the web process can query its database | `200 {"status":"ok"}` | `503 {"status":"unavailable"}` |

The endpoints contain no user, configuration, database, or exception details.
Docker Compose checks readiness every ten seconds and marks the web container
unhealthy after three consecutive failures. Liveness does not query a dependency
and is suitable for deciding whether a stuck process should be restarted.

## Logs

Application and scheduled-worker events are written as one JSON object per line
to standard error for collection by Docker or a hosting platform. Request records
include:

- UTC timestamp and severity
- logger and event name
- request correlation ID
- HTTP method, path, and response status
- request duration in milliseconds

Clients may supply `X-Request-ID`; otherwise TwitClone generates one. The value
is returned in the response header and included in the request log. Supplied
values must contain only letters, digits, periods, underscores, colons, or
hyphens and are limited to 128 characters; other values are replaced.

View local logs with:

```bash
docker compose logs -f web worker
```

Health endpoint requests are logged like other requests. Secrets, request
bodies, query strings, cookies, and authorization headers are intentionally not
logged.
