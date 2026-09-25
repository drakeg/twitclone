# Sprint 23 — API Post Lifecycle Parity

**Status:** Completed.

## Goal

Let authorized API clients manage the lifecycle of their own globally public original posts under the same safety and history semantics already established for the browser workflow.

## Story 23.1 — Owner-only API edit and soft removal

**Status:** Completed in PR #274.

- Reuse the existing `posts:write` scope rather than introducing a broader lifecycle/admin scope.
- Add `PATCH /api/v1/posts/<id>` for text-only owner edits.
- Accept exactly the `content` field and reuse the existing 144-character validation.
- Preserve original author, publication time, media, explicit topics, conversation state, and related responses.
- Refresh hashtag-derived topics and notify only newly added valid mentions.
- Set `edited_at` only when content actually changes.
- Add `DELETE /api/v1/posts/<id>` for owner-requested soft removal.
- Reuse the browser removal semantics: author actor, `Removed by author.`, no cascade deletion.
- Keep future-scheduled, Space-scoped, removed, and nonexistent posts behind the same 404 mutation boundary.
- Return `403 post_not_owned` only when a credential targets another user's currently public post.
- Apply the existing credential rate-limit budget to both mutation operations.

### Acceptance criteria

- A `posts:write` credential can edit its owner's public original post.
- A no-op edit returns the post unchanged and does not create `edited_at`.
- Edits reject unexpected fields and invalid content.
- Explicit topics survive while hashtag-derived topics refresh.
- Existing mentions are not re-notified; newly added mentions are notified once.
- Read-only credentials cannot edit or remove posts.
- A different write credential cannot mutate another user's public post.
- Non-public lifecycle states do not disclose hidden-post existence through mutation endpoints.
- Owner removal returns `204` and writes the established soft-removal metadata.
- Removed posts immediately become unavailable through the public API.
- No API restore, physical delete, media replacement, scheduling mutation, or moderation action is introduced.

## Story 23.2 — Conditional lifecycle writes

**Status:** Completed in PR #276.

- Add strong `ETag` headers to public-post GET, successful create, and successful edit responses.
- Require exact `If-Match` preconditions for PATCH and DELETE lifecycle mutations.
- Return `428 precondition_required` when a mutation omits `If-Match`.
- Return `412 precondition_failed` when the supplied ETag is stale and include the current ETag in the response.
- Include text, edit/removal state, publication identity, and public topic associations in the ETag material.
- Preserve the existing scope, ownership, privacy, and rate-limit boundaries.
- Keep POST idempotency keys outside this story; creation retry semantics are a separate concern.

### Acceptance criteria

- GET/POST/PATCH return a stable quoted ETag for the represented post state.
- A successful edit changes the ETag.
- A no-op edit keeps the same ETag.
- PATCH/DELETE without `If-Match` fail before mutation with 428.
- PATCH/DELETE with a stale ETag fail before mutation with 412.
- Browser-side topic changes make a previously issued API ETag stale.
- Existing hidden/non-public resource and cross-user authorization semantics remain unchanged.
- Tests prove stale writes cannot overwrite or remove the newer resource state.

## Story 23.3 — POST idempotency decision

**Status:** Completed by decision in this closeout.

POST idempotency is deliberately deferred.

Create retries have different semantics from PATCH/DELETE concurrency protection. A production idempotency-key contract would require persisted request keys, credential/request scoping, payload matching, replayed response storage or reconstruction, expiry/cleanup rules, conflict behavior, and abuse/storage limits. Ripple does not currently have a real integration demonstrating that duplicate create retries are causing a user-facing problem.

Adding that state now would create a new persistence and cleanup contract for speculative automation needs.

### Revisit criteria

A future story may add POST idempotency when at least one concrete integration needs safe create retries. That story must define:

- accepted `Idempotency-Key` syntax and maximum length;
- credential/user/endpoint scoping;
- payload fingerprinting and mismatch behavior;
- replay status/body/header semantics;
- retention/expiration and cleanup behavior;
- rate-limit interaction and storage-abuse limits;
- concurrency behavior for simultaneous requests using the same key; and
- tests proving a key cannot replay or authorize another credential's request.

Until then, clients should treat POST creation as non-idempotent and avoid blind retries after ambiguous network failures.

## Sprint outcome

Sprint 23 gives API clients lifecycle parity for their own globally public original posts without broadening moderation or administrative authority. API clients can create, text-edit, and soft-remove owned public posts under the existing `posts:write` scope. PATCH and DELETE are protected by strong ETag/`If-Match` preconditions so stale clients cannot overwrite or remove newer resource state.

The public API documentation now reflects the current read/write contract, privacy boundaries, rate limits, ownership rules, and conditional-write behavior.

## Definition of done

Completed. Owner lifecycle mutations are bounded, authenticated, rate-limited, privacy-preserving, and protected against lost updates. POST idempotency remains intentionally deferred until a concrete integration justifies the extra persistence and replay contract.

## Boundary

Sprint 23 does not broaden moderation/admin authority, expose non-public posts, add OAuth, provision infrastructure, or authorize paid services.
