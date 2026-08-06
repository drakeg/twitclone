# ADR-0013: Polls Blueprint

- Status: Accepted
- Date: 2026-08-05
- Sprint: 2
- Story: 2.8

## Context

Poll creation and voting remain in `app.py` after the authentication, timeline,
and messaging extractions. They form a cohesive write-oriented route group while
poll display remains part of the combined timeline query.

The current workflow uses the existing top-level `PollForm`, poll templates, and
model behavior. Validation and database hardening are planned product concerns,
not requirements for this structural extraction.

## Decision

Create `twitclone.polls` with a `polls` Blueprint owning:

- `/create_poll`
- `/vote_poll/<poll_id>`

Register both routes from the application factory with their existing endpoint
names. Preserve form validation, templates, login protection, model writes,
duration fields, option creation, duplicate-vote handling, flash messages, and
redirects.

Timeline poll rendering remains in the Timeline Blueprint. The existing
`PollForm` remains in `forms.py`. The old poll functions in `app.py` are
temporarily dormant compatibility code and no longer own URL rules in the
supported factory path.

## Consequences

### Positive

- Poll write workflows now have package route ownership.
- Existing URLs and template endpoint references remain stable.
- Poll routes use package-owned extensions and models directly.
- Timeline and poll write responsibilities remain independently reviewable.

### Negative

- Unqualified endpoint compatibility requires a Blueprint registration hook.
- Poll rendering and writes remain split across two Blueprints.
- The package temporarily imports `PollForm` from the top-level forms module.
- Dormant implementations remain until final monolith cleanup.

## Guardrails

- Voting rules, ownership validation, schema constraints, and poll expiration
  changes require separate stories.
- No templates, forms, models, migrations, dependencies, or UI change here.
- A later forms extraction must preserve field names and validation behavior.
