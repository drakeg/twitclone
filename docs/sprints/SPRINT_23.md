# Sprint 23 — API Post Lifecycle Parity

**Status:** In implementation.

## Goal

Let authorized API clients manage the lifecycle of their own globally public original posts under the same safety and history semantics already established for the browser workflow.

## Story 23.1 — Owner-only API edit and soft removal

**Status:** In implementation.

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

## Planned follow-up stories

- Evaluate whether API lifecycle responses need idempotency/conditional-write support before broader automation use.
- Audit API documentation/examples after real integration use rather than adding speculative endpoints.
- Keep API mutation scope bounded to mature browser semantics unless a separate story expands it.

## Boundary

Sprint 23 does not broaden moderation/admin authority, expose non-public posts, add OAuth, provision infrastructure, or authorize paid services.
