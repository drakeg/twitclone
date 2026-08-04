# ADR-0009: Package-owned utility boundary

- Status: Accepted
- Date: 2026-07-28
- Sprint: 2
- Story: 2.4

## Context

Reusable Gravatar, image, hashtag, user-discovery, and text-formatting helpers were defined inside the legacy `app.py` monolith. Blueprint extraction would otherwise require new package modules to import that monolith, preserving circular ownership and import-time side effects.

A complete physical rewrite of `app.py` solely to delete small helper definitions would create a large, difficult-to-review file replacement while route extraction is already planned in subsequent stories.

## Decision

Create a package-owned `twitclone.utils` boundary with focused modules:

- `gravatar.py` for Gravatar URLs
- `images.py` for thumbnail generation
- `hashtags.py` for trending hashtags and newest-user queries
- `text.py` for clickable mentions and hashtags

The supported `twitclone.create_app()` path explicitly binds the transitional legacy module's helper names to these package implementations after importing `app.py`. Existing routes, context processors, and template filters resolve those names at request time, so behavior and endpoint registration remain unchanged.

The original helper definitions may remain as dormant compatibility code until their related route groups move into blueprints. Package utilities are authoritative for the supported runtime and for all new code.

## Consequences

### Positive

- New blueprints can import helpers without importing `app.py`.
- Pure helpers can be unit tested independently.
- Database-backed discovery helpers depend on package-owned models rather than the monolith.
- The refactor avoids route, schema, template, and endpoint changes.
- Future blueprint PRs can delete legacy copies alongside the code that used them.

### Negative

- Direct unsupported execution or import of `app.py` before factory binding can still expose the legacy helper definitions.
- There is temporary source duplication until blueprint extraction removes the dormant copies.

## Guardrails

- New code imports utilities only from `twitclone.utils` or its submodules.
- Behavioral changes to hashtag ranking, image sizing, generated markup, or Gravatar formatting require separate stories.
- The compatibility binder is removed only after no supported route or template callback depends on legacy globals.
