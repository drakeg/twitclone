# ADR-0023: Direct-message reply boundary

- Status: Accepted
- Date: 2026-08-13
- Sprint: 4
- Story: 4.3

## Context

The reply route loaded Direct Messages by identifier without checking the
recipient. Any authenticated user who discovered an identifier could view the
message and send a reply to its sender. Missing content raised a request error,
blank content was accepted, and reply and notification writes used separate
transactions.

## Decision

- Only the original message recipient may view or submit its reply route.
- Unauthorized and nonexistent message identifiers both return 404.
- Reply content is required, cannot be whitespace-only, and is limited to 500
  characters on both the server and the browser form.
- A valid reply and its notification are committed in one transaction.
- Existing URLs, successful redirects, messages, and page styling are retained.

## Consequences

- Message identifiers no longer grant access to other users' conversations.
- Malformed requests fail without Direct Message or Notification writes.
- Reply and notification records cannot be partially committed.
- The legacy timeline `/dm` command remains a separate creation workflow and
  requires its own future product decision if it is retained.

## Guardrails

- Every message-detail action must scope its query to the authenticated party.
- Browser constraints complement but never replace server validation.
- New message writes that produce notifications must share one transaction.
