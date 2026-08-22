# Ripple

Ripple is a Flask-based social networking application inspired by early microblogging platforms. The current application includes user accounts, timelines, follows, posts, reposts, quotes, bookmarks, direct messages, notifications, hashtags, image uploads, scheduled posts, and polls.

> **Project status:** Active redevelopment. The immediate focus is stabilizing the existing application, documenting its architecture, improving security and test coverage, and then delivering features in small Agile sprints.
>
> **Naming note:** The product is branded as **Ripple**. The repository and internal Python package remain `twitclone` for now to avoid an unnecessary import and deployment refactor during the branding change.

## Current technology

- Python and Flask
- Flask-SQLAlchemy and Alembic/Flask-Migrate
- Flask-Login and Flask-Bcrypt
- Flask-WTF/CSRF protection
- Gunicorn for WSGI serving
- SQLite for local development and PostgreSQL for production
- APScheduler for scheduled posts
- Pillow for uploaded-image processing

## Local development

### Docker Compose (simplest)

With Docker Desktop or Docker Engine running:

```bash
docker compose up --build
```

Open <http://localhost:8000>. Compose applies database migrations before its
Gunicorn web service starts, runs scheduled-post processing in a separate
worker, and uses a named volume to preserve the SQLite database and uploaded
media.

If port 8000 is already in use by another local application, set a different
host port while leaving Ripple's internal container port unchanged:

```bash
RIPPLE_PORT=8001 docker compose up --build
```

Ripple will then be available at <http://localhost:8001>. You can also set
`RIPPLE_PORT` in a local `.env` file, for example:

```text
RIPPLE_PORT=8010
```

This makes it easy to run multiple local applications at the same time without
changing Ripple's Gunicorn or health-check ports.

### Demo users and public sample content

For a fresh local installation, populate Ripple with sample accounts and public
activity so anonymous visitors can immediately see what the network looks like:

```bash
docker compose exec web flask --app application seed-demo-content
```

The command creates eight demo users, sample posts, hashtags, `@mentions`,
follows, reposts, and quotes. It is idempotent, so running it again does not
recreate the same base content. All generated demo accounts use the local-test
password `Passw0rd!`; their email addresses use the reserved `example.test`
domain.

The demo seeder is intentionally blocked when `TWITCLONE_ENV=production`. Never
use the shared demo password for real accounts.

After pulling new changes, run the same Compose startup command; startup applies
any new database migrations before serving requests. Stop it with `Ctrl+C`; use
`docker compose down` to stop and `docker compose down -v` only when you
intentionally want to erase local data.

Use `docker compose logs -f worker` to observe scheduled-post processing.
Use `docker compose logs -f web worker` to follow structured application logs.

Compose monitors database readiness at `/health/ready`; `/health/live` provides
a dependency-free liveness signal. See
[`docs/observability.md`](docs/observability.md) for their operational contract.

See [`docs/production-serving.md`](docs/production-serving.md) for the web
process contract and the additional decisions required before public deployment.

Run the complete automated test suite in an isolated one-off container with:

```bash
docker compose run --rm test
```

The test service mounts the current checkout read-only, so this command always
tests current source and test files even when the dependency image is cached.
Rebuild after dependency-file or Dockerfile changes with
`docker compose build test`.

The test service uses an in-memory database and temporary upload directory. It
does not read, migrate, or erase the named volume used by the local application.

### Administrator access

After registering the account normally, promote it by email while Compose is
running:

```bash
docker compose exec web flask --app application make-super-admin user@example.com
```

See [`docs/administration.md`](docs/administration.md) for the non-Docker form,
expected output, production safety notes, and current revocation limitation.

### Prerequisites

- Python 3.11 or newer
- Git

### Setup

```bash
git clone https://github.com/drakeg/twitclone.git
cd twitclone
python -m venv .venv
```

Activate the virtual environment:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The production database, durable-media boundary, backup and restore runbook,
rollback procedure, preflight command, and initial cost estimate are documented.
Public deployment still requires provisioning the production resources,
migrating existing media, and completing a successful restore rehearsal.
See [`docs/database.md`](docs/database.md),
[`docs/operations.md`](docs/operations.md), and
[`docs/deployment-costs.md`](docs/deployment-costs.md).
The operations runbook links reusable release-readiness and restore-rehearsal
record templates; completed records must remain in the approved operations
system rather than this repository.

## Agile delivery model

Work is delivered through documented, reviewable increments:

1. A sprint has a clear goal and acceptance criteria.
2. Each sprint uses a dedicated branch and pull request.
3. Code, tests, migrations, configuration, and documentation ship together.
4. Unrelated files are not changed.
5. A sprint is complete only when its acceptance criteria and Definition of Done are met.

See:

- [`docs/PRODUCT_VISION.md`](docs/PRODUCT_VISION.md)
- [`docs/ROADMAP.md`](docs/ROADMAP.md)
- [`docs/AGILE_PROCESS.md`](docs/AGILE_PROCESS.md)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/sprints/SPRINT_0.md`](docs/sprints/SPRINT_0.md)

## Near-term roadmap

- **Sprint 0:** Repository assessment, documentation, backlog, and delivery standards
- **Sprint 1:** Secure and reproducible development baseline
- **Sprint 2:** Application structure and automated test foundation
- **Sprint 3:** Core timeline and post reliability
- **Sprint 4:** Social interactions and notifications
- **Sprint 5:** Media, polls, and scheduled-post hardening
- **Sprint 6:** Deployment readiness and operational documentation
- **Sprint 7:** Accessible interaction and content

## Security notice

This repository is currently a development project. Production serving and
recovery contracts and the durable object-storage adapter are defined, but
production resources, media migration, a passing deployment preflight, and a
successful restore rehearsal are still required before public deployment.

## License

No license has been selected yet. Until a license is added, all rights remain with the repository owner.
