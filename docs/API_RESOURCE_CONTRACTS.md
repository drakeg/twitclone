# Ripple Public API v1 — Resource Contracts

## Scope

Story 16.4 introduces Ripple's first bounded write contract while preserving the existing public post read contract.

### Read one public post

`GET /api/v1/posts/<id>` remains publicly readable and rate limited. A post is returned only when it is globally public: it must not be removed, future-scheduled, or scoped to a Ripple Space.

The response exposes only the stable v1 post contract: ID, type, content, public author identity, publication time, nullable edit time, public topic associations, and public post URL.

`edited_at` is `null` for never-edited posts and an ISO-8601 UTC timestamp for posts changed through Ripple's owner-only edit workflow. It is additive metadata; it does not expose prior wording.

### Create a public post

`POST /api/v1/posts` requires a valid bearer credential with the `posts:write` scope.

Accepted JSON fields:

- `content` — required, nonblank, maximum 144 characters;
- `conversation_intent` — optional string using Ripple's existing conversation-intent vocabulary; unknown values normalize to the existing `open` default;
- `topics` — optional array of at most five strings, normalized through Ripple's existing explicit-topic logic.

A successful create returns `201 Created`, the same bounded public post representation used by the read endpoint, and a `Location` header pointing at `/api/v1/posts/<id>`.

API-created posts are ordinary global Ripple posts. They participate in existing mention notifications, conversation intent, explicit-topic association, moderation, reporting, and public visibility rules. They do not receive special ranking, reputation, verification, or paid treatment.

### Edit an owned public post

Sprint 23 adds `PATCH /api/v1/posts/<id>` for the credential owner's globally public original posts. It requires `posts:write` and accepts exactly one JSON field:

- `content` — required, nonblank, maximum 144 characters.

Edits reuse Ripple's existing owner-only post lifecycle semantics: original publish identity is preserved, `edited_at` is updated only when text changes, hashtag-derived topics are refreshed while explicit topics remain intact, and only newly added valid @mentions generate notifications.

### Remove an owned public post

Sprint 23 adds `DELETE /api/v1/posts/<id>` for the credential owner's globally public original posts. It requires `posts:write` and performs the same soft-removal contract used by the browser workflow:

- `is_removed = true`;
- `removed_at` is recorded;
- `removed_by_id` is the author/credential owner; and
- `removal_reason` is `Removed by author.`.

A successful removal returns `204 No Content`. Existing relational/moderation history is retained, and the removed post is no longer readable through the public API.

### Mutation privacy and visibility

Mutation endpoints operate only on globally public original posts. Future-scheduled, Space-scoped, already removed, or nonexistent posts return the same 404-style resource boundary before ownership is evaluated. A different credential attempting to modify another currently public post receives `403 post_not_owned`.

## Deliberate exclusions

The API still does not expose media replacement/upload, scheduling changes, replies, reposts, polls, Space posting, moderation actions, billing, verification, credential self-service, OAuth, admin capabilities, restore/undo, or physical erasure.

Those workflows have additional state and authorization semantics and require separately specified contracts rather than accidental ORM exposure.

## Scope boundaries

- `posts:read` allows protected read/account operations already defined by Story 16.2.
- `posts:write` allows bounded create, owner edit, and owner soft-removal operations for global original posts.
- A read-only credential cannot create a post.
- Browser session authentication is not an API credential.
- Credentials remain independently expiring and revocable.
- Existing credential rate limits apply to write calls.

## Compatibility

The v1 contract is explicit and additive. Internal model fields are not serialized wholesale. New internal columns do not automatically become public API fields, and existing v1 clients do not need to understand unrelated Ripple model changes.

Sprint 22 adds nullable `edited_at` to the public post representation so API consumers receive the same edit-state signal as web viewers. Sprint 23 then authorizes bounded owner edit/removal under the existing `posts:write` scope without adding a broader privilege.

No migration, paid service, AWS activation, or recurring infrastructure cost is introduced by the Sprint 23 lifecycle mutation contract.
