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

## Deliberate exclusions

Story 16.4 does not expose API media upload, scheduling, deletion, editing, replies, reposts, polls, Space posting, moderation actions, billing, verification, credential self-service, OAuth, or admin capabilities.

Those workflows have additional state and authorization semantics and require separately specified contracts rather than accidental ORM exposure.

## Scope boundaries

- `posts:read` allows protected read/account operations already defined by Story 16.2.
- `posts:write` allows the bounded post-create operation only.
- A read-only credential cannot create a post.
- Browser session authentication is not an API credential.
- Credentials remain independently expiring and revocable.
- Existing credential rate limits apply to write calls.

## Compatibility

The v1 contract is explicit and additive. Internal model fields are not serialized wholesale. New internal columns do not automatically become public API fields, and existing v1 clients do not need to understand unrelated Ripple model changes.

Sprint 22 adds nullable `edited_at` to the public post representation so API consumers receive the same edit-state signal as web viewers. This does not authorize API editing or deletion.

No migration, paid service, AWS activation, or recurring infrastructure cost is introduced by Story 16.4.
