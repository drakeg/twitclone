# ADR-0024: Social interaction regression boundary

- Status: Accepted
- Date: 2026-08-14
- Sprint: 4
- Story: 4.4

## Context

Sprint 4 hardened duplicate relationships, notification state, and message
replies in focused stories. The behaviors also need coverage as one user-facing
flow so future changes cannot preserve each route independently while breaking
their shared ownership or notification contract.

The Bookmark model additionally exposed two competing user relationships:
`bookmark_user` through `User.bookmarks` and `user` through
`bookmark_relationships`. They represented the same foreign key, produced ORM
warnings, and left ownership ambiguous.

## Decision

- Add an end-to-end regression covering follow, bookmark, retweet, reply,
  message-inbox, and notification-inbox behavior across two users.
- Verify relationship deduplication and ownership together.
- Verify interaction notifications start unread and become read only when their
  owner opens the notification inbox.
- Replace the duplicate Bookmark mappings with one explicit
  `User.bookmarks` / `Bookmark.user` `back_populates` pair.

## Consequences

- Sprint 4 behavior is protected both by focused tests and a cross-feature flow.
- Bookmark ownership has one canonical ORM path and no overlapping relationship
  warnings.
- The database schema, URLs, templates, redirects, and UI remain unchanged.
- Code using the unused `bookmark_user` or `bookmark_relationships` aliases would
  need to move to the canonical names; no application code uses those aliases.

## Guardrails

- New social interactions must test ownership, duplicate behavior, generated
  notifications, and cross-user isolation together where applicable.
- A model foreign key should have one canonical writable ORM relationship.
