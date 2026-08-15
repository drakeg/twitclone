# ADR-0027: Unique poll votes

- Status: Accepted
- Date: 2026-08-15
- Sprint: 5
- Story: 5.3

## Context

The voting route checked for an existing vote, but concurrent requests could
both pass that check. The database allowed multiple votes by one user in one
poll, and the route accepted an option belonging to a different poll.

## Decision

- Enforce one `PollVote` per `(poll_id, user_id)` in the model and database.
- Keep the route's friendly duplicate check and handle constraint races safely.
- Require the submitted option to belong to the poll in the route URL.
- During migration, retain the oldest duplicate vote and recalculate all option
  counters from the retained vote rows before adding the constraint.

## Consequences

- Duplicate votes are prevented under both ordinary and concurrent requests.
- Vote counters are repaired as part of migration.
- Docker Compose remains current because its startup command automatically runs
  this migration before starting Flask.

## Guardrails

- Vote totals must remain derived from valid `PollVote` records.
- Future vote-changing behavior must preserve the unique poll/user boundary.
