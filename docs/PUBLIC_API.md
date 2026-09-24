# Ripple Public API v1

Ripple's public API is versioned under `/api/v1` and remains deliberately bounded. Internal Flask routes, ORM models, templates, and database schemas are not public contracts unless explicitly documented here.

## Endpoints

### `GET /api/v1/`

Returns API metadata including the supported bearer-token scopes.

### `GET /api/v1/posts/{id}`

Returns one globally public original post under a `data` envelope with these fields: `id`, `type`, `content`, public `author` identity, `published_at`, nullable `edited_at`, public `topics`, and `url`.

The endpoint returns `404 post_not_found` when the row is missing or is not eligible for the global public surface, including removed posts, future-scheduled posts, and posts scoped to a Ripple Space.

### `POST /api/v1/posts`

Requires a bearer credential with `posts:write`. Creates one ordinary globally public original post using Ripple's existing content validation, conversation-intent normalization, topic association, and mention-notification behavior.

### `PATCH /api/v1/posts/{id}`

Requires `posts:write` and ownership of the currently public original post. Accepts exactly:

```json
{"content": "updated post text"}
```

The edit is text-only. It preserves original publication identity and explicit topics, refreshes hashtag-derived topics, notifies only newly added mentions, and sets `edited_at` only when content actually changes.

### `DELETE /api/v1/posts/{id}`

Requires `posts:write` and ownership of the currently public original post. Performs author soft removal and returns `204 No Content`. It does not physically delete relational/moderation history.

### `GET /api/v1/account`

Requires a bearer credential with `posts:read` and returns the credential owner's bounded account/credential metadata.

## Authentication and scopes

Bearer credentials use the `Authorization: Bearer <token>` header.

Current scopes:

- `posts:read` — protected account/read operations.
- `posts:write` — bounded create, owner edit, and owner soft-removal operations for globally public original posts.

A write credential does not grant moderation, admin, Space, billing, verification, or private-data authority.

## Mutation visibility boundary

Mutation endpoints fail closed for non-public resources. Future-scheduled, Space-scoped, already removed, and nonexistent posts return `404` before ownership is evaluated. A different credential targeting another user's currently public post receives `403 post_not_owned`.

## Rate limits

Public reads, invalid-token attempts, and valid credentials use the existing independent fixed-window API budgets. Lifecycle mutations consume the credential's normal API budget; they do not bypass or create a privileged rate path.

## Error envelope

Documented API errors use:

```json
{
  "error": {
    "code": "post_not_found",
    "message": "The requested public post was not found."
  }
}
```

Clients should branch on `error.code` rather than human-readable message text.

## Versioning

`v1` is the compatibility boundary. Additive fields may be introduced when they do not change existing meaning. Removing fields or making incompatible semantic changes requires a separately versioned contract.

## Visibility and privacy

The API fails closed. A database row is not automatically a public API resource. New content types require explicit API visibility review before exposure.

The current contract does not expose email addresses, passwords, administrative state, subscription or entitlement state, moderation internals, private messages, private analytics, removed content, or unbounded ORM relationships.

## Deliberate exclusions

The API does not currently provide media replacement/upload, scheduling mutation, replies, reposts, polls, Space posting, moderation actions, restore/undo, physical erasure, billing, verification, credential self-service, OAuth, or admin capabilities.

## Integrity boundaries

API access does not alter organic feed placement, reputation, verification, moderation authority, report priority, or safety behavior. Paid status does not unlock hidden public data or preferential API ranking.
