# ADR-0015: Final route boundaries and legacy cleanup

- Status: Accepted
- Date: 2026-08-06
- Sprint: 2
- Story: 2.10

## Context

After the authentication, timeline, messaging, polls, and notifications
extractions, `app.py` still owns profile/social, discovery, and bookmark routes.
It also retains dormant copies of previously extracted routes and utilities.

Those copies obscure runtime ownership and keep the legacy module much larger
than its remaining startup and compatibility responsibilities require.

## Decision

Create three final package-owned Blueprints:

- `twitclone.profiles` for profile editing, follows, unfollows, and relationship
  lists
- `twitclone.discovery` for search and hashtag results
- `twitclone.bookmarks` for bookmark creation and listing

Register every route with its existing unqualified endpoint name. Preserve URLs,
methods, templates, redirects, login protection, model writes, notifications,
ordering, filtering, flash messages, and JSON response shapes.

Remove all dormant route implementations and duplicate utility implementations
from `app.py`. Retain only transitional application construction, extension and
model compatibility exports, scheduler startup, the login loader, template
context/filter callbacks, and direct-run startup through the supported factory.

## Consequences

### Positive

- Every application route now has package ownership.
- `app.py` has a small, explicit transitional purpose.
- New route code no longer imports the legacy module.
- Existing endpoint and template contracts remain stable.
- Source-level tests prevent route ownership from returning to `app.py`.

### Negative

- Unqualified endpoint compatibility still requires Blueprint registration
  hooks.
- Scheduler and initial Flask object construction remain transitional legacy
  responsibilities.
- Several preserved behaviors still warrant later validation and security work.

## Guardrails

- User-visible behavior changes require later product stories.
- No templates, models, forms, migrations, dependencies, or UI change here.
- New routes belong in package Blueprints, never in `app.py`.
- Compatibility exports may be removed only through a coordinated startup,
  migration, and test-fixture change.
