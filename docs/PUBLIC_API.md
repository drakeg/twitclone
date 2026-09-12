# Ripple Public API v1

Ripple's public API is versioned under `/api/v1` and begins as a deliberately small read-only preview. Internal Flask routes, ORM models, templates, and database schemas are not public contracts unless explicitly documented here.

## Endpoints

### `GET /api/v1/`

Returns API metadata with `name`, `version`, `status`, and `documentation` fields.

### `GET /api/v1/posts/{id}`

Returns one globally public post under a `data` envelope with these fields: `id`, `type`, `content`, `author` (`id` and `username`), `published_at`, `topics`, and `url`.

The endpoint returns `404` with error code `post_not_found` when the row is missing or is not eligible for the global public surface, including removed posts, posts scheduled for the future, and posts scoped to a Ripple Space.

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

The current contract does not expose email addresses, passwords, administrative state, subscription or entitlement state, moderation internals, private messages, private analytics, or unbounded ORM relationships.

## Authentication and writes

No API credential or write contract exists in Story 16.1. Browser session cookies are not a supported API authentication strategy. Protected/write operations wait for scoped authentication and revocation in Story 16.2 plus rate/abuse controls in Story 16.3.

## Integrity boundaries

API access does not alter organic feed placement, reputation, verification, moderation authority, report priority, or safety behavior. Paid status does not unlock hidden public data or preferential API ranking.
