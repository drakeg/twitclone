# ADR-0053: Bounded owner post lifecycle through API v1

- Status: Accepted
- Date: 2026-09-24
- Sprint: 23
- Story: 23.1

## Context

Ripple API v1 already supports public post reads and scoped creation through bearer credentials. Sprint 21 established owner-only browser semantics for original-post text editing and soft removal, and Sprint 22 exposed edit state in the public representation.

Without lifecycle mutation support, API-created posts cannot be corrected or withdrawn through the same integration that created them. Adding generic update/delete access, however, would risk turning `posts:write` into an accidental broad mutation scope.

## Decision

Reuse `posts:write` for two narrowly bounded owner operations on globally public original posts:

- `PATCH /api/v1/posts/<id>` — text-only owner editing.
- `DELETE /api/v1/posts/<id>` — owner-requested soft removal.

The operations inherit established browser semantics.

Edits:

- validate the 144-character post-content contract;
- accept only `content`;
- preserve publication identity, media, explicit topics, conversation state, and related history;
- refresh hashtag-derived topic associations;
- notify only newly added mentions; and
- set `edited_at` only after a real content change.

Removal:

- sets the existing soft-removal fields;
- records the credential owner as the removing author;
- uses `Removed by author.`; and
- does not cascade-delete related history.

Mutation eligibility is checked against the existing global-public-post boundary before ownership. Future-scheduled, Space-scoped, removed, and missing posts therefore share a 404 resource boundary. Another credential targeting a different user's currently public post receives `403 post_not_owned`.

All operations use the existing credential rate limit.

## Consequences

### Positive

- API clients can correct or withdraw posts they own.
- Web and API lifecycle behavior share the same user-facing semantics.
- No new broad privilege or admin scope is introduced.
- Hidden/non-public resources remain outside the mutation API.
- Existing abuse-rate controls continue to apply.

### Constraints

- API editing is text-only.
- API removal is soft removal, not physical erasure.
- No restore/undo endpoint exists.
- No media, scheduling, reply, poll, repost, Space, or moderation mutation is authorized by this decision.
- `posts:write` remains intentionally bounded to mature original-post lifecycle behavior.

## Follow-up

Broader automation capabilities require separate contracts. Idempotency keys, conditional writes, OAuth, or additional mutable content types should be introduced only when an integration need justifies their complexity and security review.


## Conditional-write follow-up

Sprint 23 Story 23.2 adds strong ETag preconditions before wider automation use.

Public post GET, successful create, and successful edit responses return an ETag derived from the mutable public representation. PATCH and DELETE require the exact current ETag through `If-Match`; missing preconditions return 428 and stale preconditions return 412.

This guards against lost updates between concurrent clients or browser/API workflows without expanding the `posts:write` privilege. POST idempotency is intentionally not bundled into this decision because duplicate-create retry semantics require a separate request-key/storage contract.
