# ADR-0007: Own Flask extensions in the application package

- Status: Accepted
- Date: 2026-07-24

## Context

TwitClone originally defined and initialized SQLAlchemy, Flask-Migrate, Bcrypt,
Flask-Login, and CSRF inside the legacy `app.py` monolith. Models, tests,
migrations, and future blueprints require one stable extension registry that does
not depend on importing the monolith first.

The first Story 2.2 slice established `twitclone.extensions` as a stable import
boundary while retaining the original objects. That allowed the ownership move
to happen separately from model and route extraction.

## Decision

`twitclone/extensions.py` owns one unbound instance of each Flask extension:

```python
from twitclone.extensions import db, migrate, bcrypt, login_manager, csrf
```

The objects are created without a Flask application. After validated
configuration is loaded, `init_extensions(app)` binds all five objects to the
configured application.

The legacy `app.py` module temporarily re-exports the imported names because
existing models, routes, migrations, and tests still import from that module.
Those compatibility exports will disappear as later Sprint 2 stories move the
remaining code into the package.

## Consequences

### Positive

- SQLAlchemy models and migrations share one package-owned metadata registry.
- Extension creation no longer occurs inside the route/model monolith.
- Future blueprints and models have a stable import path.
- Configuration remains authoritative before extension initialization.
- Tests can verify that no duplicate security or persistence objects exist.

### Temporary limitations

- `app.py` still owns models, routes, helper functions, and scheduler setup.
- The current factory still returns the transitional application singleton.
- Multiple independent application instances remain a later factory goal.

## Rejected alternatives

### Duplicate package and monolith instances

Creating new extension objects in the package while leaving the original objects
active in `app.py` was rejected because it would split SQLAlchemy metadata,
migration discovery, authentication state, and CSRF handling.

### Move extensions, models, and routes together

A single large rewrite was rejected because it would combine multiple Sprint 2
stories and make regressions difficult to isolate.

## Validation

Tests verify that:

- imports from `twitclone.extensions` and compatibility exports from `app.py`
  reference the same objects;
- SQLAlchemy remains registered with the configured application;
- existing model metadata remains populated;
- `app.py` no longer constructs Flask extension instances;
- the login view remains unchanged.
