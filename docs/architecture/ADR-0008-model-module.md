# ADR-0008: Move SQLAlchemy models into the application package

- Status: Accepted
- Date: 2026-07-25

## Context

TwitClone historically defined every SQLAlchemy model inside `app.py` alongside
configuration, extension initialization, scheduler setup, helper functions, and
routes. That structure made migrations and future blueprints depend on importing
the entire legacy application module.

ADR-0007 moved the shared Flask extension objects into `twitclone.extensions`.
The next safe boundary is to move the model definitions onto that shared database
registry before route extraction begins.

## Decision

All persistent domain models are defined in `twitclone/models.py` and import the
shared `db` object from `twitclone.extensions`.

The legacy `app.py` module temporarily imports and re-exports those model classes.
This compatibility layer preserves existing route code, tests, migration loading,
and any external imports while later Sprint 2 stories move routes into
blueprints.

No model redesign is included. Column definitions, inferred table names,
relationships, backrefs, defaults, and model methods remain unchanged.

New code should import models from:

```python
from twitclone.models import User, Tweet
```

## Consequences

### Positive

- Models no longer require importing the route monolith.
- Migrations and future blueprints share one explicit metadata registry.
- Route extraction can proceed without relocating model declarations at the same
  time.
- Model tests can validate schema metadata independently of route behavior.

### Temporary limitations

- `app.py` still imports and re-exports every model for compatibility.
- The Flask-Login user loader remains registered in `app.py` until authentication
  routes and lifecycle hooks are extracted.
- Models remain in one module; splitting them by domain is intentionally deferred.

## Schema compatibility

This is a source-code relocation only. It must not produce a new Alembic
revision. The existing migration remains authoritative and the table inventory
must remain:

- `user`, `follows`
- `tweet`, `retweet`, `quote`
- `direct_message`, `notification`
- `bookmark`
- `poll`, `poll_option`, `poll_vote`

## Validation

Regression tests verify:

- `app.py` exports the exact package-owned classes
- the complete table and column inventory
- relationship registration
- Flask-Login user loading
- absence of model declarations in the legacy module
- the existing migration can still initialize a clean database
