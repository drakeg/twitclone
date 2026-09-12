# Ripple Public API v1

Ripple's public API is versioned under `/api/v1` and begins as a deliberately small read-only preview. The contract is intended for external clients and automation; internal Flask routes, ORM models, templates, and database schemas are not part of the public API unless explicitly documented here.

## Current endpoints

### `GET /api/v1/`

Returns API metadata:

```json
{
  "name": "Ripple Public API",
  "version": "v1",
  "status": "read-only-preview",
  "documentation": "/api/v1/"
}
```

### `GET /api/v1/posts/{id}`

Returns one globally public post:

```json
{
  "data": {
    "id": 123,
    "type": "post",
    "content": "Example post",
    "author": {
      "id": 42,
      "username": "example"
    },
    "published_at": "2026-09-12T00:00:00Z",
    "topics": [
      {
        "name": "AWS",
        "slug": "aws",
        "source": "explicit"
      }
    ],
    "url": "/post/123"
  }
}
```

The endpoint returns `404` with code `post_not_found` when the requested post is missing or is not eligible for the global public surface. That includes removed posts, posts scheduled for the future, and posts scoped to a Ripple Space.

## Error envelope

Documented API errors use this shape:

```json
{
  "error": {
    "code": "post_not_found",
    "message": "The requested public post was not found."
  }
}
```

Clients should branch on `error.code`; human-readable messages may be clarified without creating a new API version.

## Versioning

`v1` is the compatibility boundary. New additive fields may be introduced within v1 when they do not change the meaning of existing fields. Removing fields, changing field meaning, or making incompatible behavior changes requires a separately versioned contract.

## Visibility and privacy

The API fails closed. A database row is not automatically a public API resource. API visibility must match Ripple's product visibility rules, and new content types must receive explicit API visibility review before exposure.

The current contract does not expose email addresses, passwords, administrative state, subscription or entitlement state, moderation internals, private messages, private analytics, or unbounded ORM relationships.

## Authentication and writes

No API credential or write contract exists in Story 16.1. Browser session cookies are not a supported API authentication strategy. Protected or write operations must wait for the scoped authentication/revocation work in Story 16.2 and the rate/abuse controls in Story 16.3.

## Ranking and commercial boundaries

API access does not alter organic feed placement, topic/community reputation, verification, moderation authority, report priority, or safety behavior. Paid status does not unlock hidden public data or preferential API ranking.
