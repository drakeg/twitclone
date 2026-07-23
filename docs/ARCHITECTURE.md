# Architecture

## Current state

TwitClone is currently a Flask monolith backed by SQLite. Most application configuration, database models, scheduling, utility functions, and routes are held in a single application module. HTML templates and static assets provide the browser interface.

## Current components

- **Web framework:** Flask
- **Persistence:** Flask-SQLAlchemy with SQLite
- **Migrations:** Flask-Migrate/Alembic
- **Authentication:** Flask-Login and Flask-Bcrypt
- **Forms and CSRF:** Flask-WTF
- **Background scheduling:** APScheduler running with the web application
- **Media:** Local filesystem uploads processed by Pillow
- **Presentation:** Server-rendered Jinja templates and static assets

## Existing domain capabilities

- Users and authentication
- Following relationships
- Posts, reposts, and quotes
- Likes and bookmarks
- Direct messages and notifications
- Hashtag discovery
- Image uploads
- Scheduled posts
- Polls and votes

## Known architectural risks

### Configuration and secrets

The application currently defines development configuration in source code, including a hard-coded secret. This must be replaced before public deployment.

### Single-module concentration

Models, routes, configuration, scheduler startup, and utility functions are tightly coupled. This makes testing and controlled startup difficult and increases regression risk.

### Scheduler lifecycle

Starting APScheduler during module import can create duplicate scheduler processes under reloaders or multi-worker servers. Scheduled work should eventually run in a separately controlled process.

### Local media storage

Uploaded files are stored under the application filesystem. Validation, collision handling, retention, backups, and production persistence require explicit design.

### Database constraints

Application-level checks may not fully prevent duplicate follows, votes, bookmarks, likes, or other relationships. Important invariants should be enforced at the database level.

### Timeline query complexity

The timeline combines several content types. Its ordering, authorization, media fields, scheduled visibility, pagination, and rendering behavior require tests before refactoring.

### Dependency lifecycle

The repository has multiple overlapping automated dependency pull requests. Dependencies should be reconciled as a tested set rather than merging historical bot PRs independently.

## Target direction

The near-term target remains a modular Flask monolith:

- Application factory
- Environment-based configuration
- Explicit extension initialization
- Separate models, services, and blueprints
- Automated tests and CI
- Controlled background-worker entry point
- SQLite for local development and a production-capable relational database only when deployment begins

This approach improves maintainability without introducing distributed-system cost or complexity prematurely.

## Architecture decision policy

Significant decisions should be recorded under `docs/decisions/` when they affect security, data storage, deployment, operating cost, external services, or major application structure.
