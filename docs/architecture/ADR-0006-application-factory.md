# ADR-0006: Introduce a Transitional Application Factory

- **Status:** Accepted
- **Date:** 2026-07-23
- **Sprint:** Sprint 2 — Architecture Modernization

## Context

TwitClone currently defines its Flask application, extensions, models, routes, and scheduler in the top-level `app.py` module. Configuration and tests have been improved, but the supported entry point still imports that global application directly.

A conventional Flask package named `app` cannot safely be introduced while `app.py` exists because the module and package would compete for the same import name. Renaming and restructuring the entire monolith in one pull request would create unnecessary regression risk.

## Decision

Introduce a neutral `twitclone` package containing `create_app()`.

For this first architecture slice, the factory:

1. validates environment-backed configuration;
2. lazily imports the existing legacy application;
3. applies the validated configuration;
4. creates the configured upload directory;
5. disables the scheduler when configuration requires it; and
6. returns the configured Flask application.

`application.py` becomes a thin WSGI and local-development entry point that calls the factory.

## Consequences

### Positive

- There is one documented application construction path.
- WSGI deployment and tests use the same entry point.
- Configuration validation occurs before the supported application is exposed.
- Later refactors can move extensions, models, routes, and scheduler responsibilities behind the factory incrementally.
- Existing endpoints, templates, models, and database migrations remain unchanged.

### Transitional limitations

- The factory currently returns the legacy application singleton rather than creating multiple independent Flask instances.
- `app.py` still contains import-time initialization and scheduler behavior.
- Complete application-factory isolation requires later Sprint 2 stories for extensions, scheduler, models, and blueprints.
- The future package remains named `twitclone` unless and until the legacy `app.py` name is retired.

## Alternatives considered

### Rename `app.py` and create an `app/` package immediately

Rejected for this story because it would require simultaneous route, template-root, extension, migration, and import changes across the full monolith.

### Leave `application.py` as a configuration wrapper

Rejected because it does not provide a stable construction API for tests, WSGI servers, and future modularization.

## Follow-up work

- Move extension objects into a dedicated module.
- Eliminate scheduler import-time startup.
- Move models behind the package boundary.
- Convert route groups to blueprints.
- Remove the legacy hard-coded secret assignment tracked by Issue #29.
