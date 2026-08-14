# ADR-0021: Unique social relationships

- Status: Accepted
- Date: 2026-08-13
- Sprint: 4
- Story: 4.1

## Context

Repeated follow, bookmark, and retweet requests could attempt to create the same
relationship more than once. Follow pairs already use a composite primary key,
but the route could still raise an integrity error and emit repeated
notifications. Bookmarks and Retweets had neither route-level duplicate checks
nor database uniqueness constraints.

Quotes are authored content rather than relationship records. Poll-vote
uniqueness is reserved for Sprint 5, where vote counting and constraints can be
handled together.

## Decision

Treat follow, unfollow, bookmark, and retweet requests as idempotent:

- repeated requests preserve their existing response format and redirects;
- only the first state change writes a relationship or notification;
- Bookmark and Retweet enforce one row per user and Tweet in the database; and
- the migration retains the oldest existing row in each duplicate group before
  adding the constraints.

## Consequences

- Retries and double-clicks no longer create duplicate rows or notifications.
- Database constraints protect against concurrent requests that pass route-level
  checks at the same time.
- Existing duplicate Bookmark or Retweet rows are collapsed during migration.
- Users cannot intentionally create multiple Retweets of the same Tweet under
  the current interaction model.

## Guardrails

- New relationship-style interactions require idempotent route behavior and a
  database uniqueness boundary.
- Content records such as Quotes must not be deduplicated merely because they
  reference the same Tweet.
- Poll voting remains governed by its dedicated Sprint 5 story.
