# ADR-0007: Introduce a stable Flask extension import boundary

- Status: Accepted
- Date: 2026-07-24

## Context

TwitClone currently defines and initializes SQLAlchemy, Flask-Migrate, Bcrypt,
Flask-Login, and CSRF inside the legacy `app.py` monolith. Models, tests,
migrations, and future blueprints need a stable place to import those objects
before the monolith can be split safely.

Moving the definitions and all dependent code in one change would create a
large, difficult-to-review refactor. The repository also still relies on
`app.py` for all models and routes.

## Decision

Add `twitclone/extensions.py` as the supported import boundary for shared Flask
extensions.

During the first slice, the module lazily returns the active objects initialized
by `app.py`. This preserves object identity and avoids duplicate SQLAlchemy or
Flask extension instances.

New and migrated code should import extension objects from:

```python
from twitclone.extensions import db, migrate, bcrypt, login_manager, csrf
```

The next extension-refactor slice will move the unbound object definitions into
`twitclone/extensions.py` and initialize them through the application lifecycle.
Because callers already use the stable import path, that move will not require
another broad import rewrite.

## Consequences

### Positive

- Establishes one supported import location.
- Preserves the exact extension objects currently used by models and migrations.
- Reduces risk and review size for the eventual definition move.
- Allows model and blueprint extraction to begin using package imports.

### Temporary limitations

- Importing an extension still loads the legacy `app.py` module.
- Extension definitions and initialization remain in the monolith.
- Multiple independent application instances are not yet supported.

## Rejected alternative

Move every extension definition and all dependent model, migration, fixture,
and route imports in one PR. This was rejected because it would combine several
Sprint 2 stories and make behavior regressions harder to isolate.

## Validation

Tests verify that every object imported through `twitclone.extensions` is the
same object exported by the current application module and that SQLAlchemy is
registered with the configured Flask application.
