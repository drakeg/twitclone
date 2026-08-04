# ADR-0010: Authentication Blueprint

- Status: Accepted
- Date: 2026-08-03
- Sprint: 2
- Story: 2.5

## Context

The legacy `app.py` module owns every application route. Authentication is a
small, cohesive route group with no scheduler, image, timeline, messaging, or
notification responsibilities, making it a low-risk first Blueprint boundary.

Existing templates and Flask-Login configuration refer to the unqualified
`login`, `logout`, and `register` endpoint names. Changing those names would
expand this refactor into template and UI work.

## Decision

Create `twitclone.auth` with an `auth` Blueprint and package-owned route
implementations for `/login`, `/logout`, and `/register`. Register the Blueprint
from the supported application factory after the transitional legacy module is
loaded.

The Blueprint registration hook adds the three URL rules with their existing
unqualified endpoint names. URLs, templates, redirects, form fields, flash
messages, password hashing, and database behavior therefore remain unchanged.

Future route groups should use package-owned Blueprints, depend on shared
extensions and models, and avoid importing the legacy `app.py` module.

## Consequences

### Positive

- Authentication routes have a cohesive package boundary.
- The first Blueprint establishes a pattern for incremental route extraction.
- Existing endpoint names keep templates and Flask-Login configuration stable.
- The legacy module no longer owns authentication implementations.

### Negative

- Preserving unqualified endpoints requires a Blueprint registration hook
  instead of the usual Blueprint-prefixed endpoint names.
- The application factory still imports the legacy module while other routes
  remain there.

## Guardrails

- Authentication behavior changes require a separate story.
- Templates, models, dependencies, migrations, and UI remain outside this story.
- The legacy endpoint-name compatibility can be reconsidered only with a
  coordinated template and Flask-Login migration.
