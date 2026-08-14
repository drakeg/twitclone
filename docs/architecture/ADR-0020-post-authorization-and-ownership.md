# ADR-0020: Post authorization and ownership boundaries

- Status: Accepted
- Date: 2026-08-13
- Sprint: 3
- Story: 3.5

## Context

Twitclone creates Tweets, Retweets, Quotes, and Bookmarks through authenticated
routes. Each created row must belong to the authenticated user, regardless of
additional form fields supplied by a client. This is an important boundary
because browser forms are not a security boundary and requests can be crafted
without using the application UI.

The application does not currently expose Tweet edit or delete routes. Adding
such behavior solely to demonstrate an ownership check would expand this story
beyond regression coverage and change the product surface.

## Decision

Define and test the current post-write boundary:

- anonymous requests cannot create Tweets, Retweets, Quotes, or Bookmarks;
- every new post or interaction derives its owner from `current_user`;
- a submitted `user_id` is ignored and cannot transfer ownership; and
- interactions continue to target the Tweet selected by the route URL.

These tests exercise the public HTTP routes and verify the persisted database
rows. Existing URLs, templates, redirects, models, dependencies, and UI remain
unchanged.

## Consequences

### Positive

- Authentication regressions across all current post writes are detected.
- Client-controlled identity fields cannot silently become trusted later.
- Ownership expectations are explicit before edit or delete workflows exist.
- Sprint 3 closes with coverage for its current authorization surface.

### Negative

- The checks remain route-level rather than a reusable authorization policy.
- There is no owner-only mutation test until owner-only mutations are added.

## Guardrails

- Future post mutations must require authentication and authorize the persisted
  resource owner before making changes.
- Ownership must never be accepted from request form, query-string, or JSON
  identity fields.
- New interaction types must receive equivalent anonymous-access and ownership
  regression coverage.

## Deferred work

- Tweet editing and deletion require separate product stories.
- Duplicate interaction rules and database constraints are separate concerns.
- Direct-message authorization belongs to Sprint 4.
