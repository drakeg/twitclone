# Ripple API authentication

Sprint 16 Story 16.2 introduces Ripple's first-party bearer credential foundation for protected API operations.

## Credential contract

- Bearer tokens use the `rpl_` prefix and are displayed only at creation time.
- Ripple stores only a SHA-256 digest plus a short non-secret prefix for identification; the raw bearer token is not persisted.
- Credentials have explicit scopes. The first supported scope is `posts:read`.
- Credentials expire after 90 days by default and may not exceed 365 days.
- Credentials can be revoked independently without changing the Ripple user's password or browser sessions.
- Successful bearer authentication records `last_used_at` for auditability.
- Revoked, expired, malformed, and unknown credentials fail closed.
- Browser login cookies do not satisfy protected API authentication. Protected operations require an `Authorization: Bearer <token>` header.

## Operator workflow

Story 16.2 intentionally uses an operator CLI for credential lifecycle management while Ripple's integration surface is still a preview. The CLI reveals a new token once and never lists raw bearer secrets afterward.

```bash
flask api_v1 credential-create user@example.com --label "local integration"
flask api_v1 credential-list user@example.com
flask api_v1 credential-revoke user@example.com 1
```

`credential-create` accepts `--days 1..365` and defaults to 90 days. All credentials currently receive only the `posts:read` scope.

## Protected authentication probe

`GET /api/v1/account` requires `posts:read` and returns bounded account/credential metadata. It exists to exercise the authentication contract before broader protected resources are authorized.

Example request:

```text
Authorization: Bearer rpl_<secret>
```

Failure semantics:

- `401 invalid_token` — missing, malformed, unknown, expired, or revoked bearer token.
- `403 insufficient_scope` — valid credential without the required operation scope.

## Security and product boundaries

- Story 16.2 does not add public write endpoints.
- No password, email address, token digest, admin state, payment state, entitlement data, or moderation state is returned by the protected API probe.
- API credentials do not affect feed ranking, reputation, verification, moderation authority, safety behavior, or paid reach.
- API credentials are application secrets and should not be committed to source control, logs, screenshots, support tickets, or client-side browser code.
- Token rotation is create-new, update the integration, then revoke-old.
- Rate limiting and broader abuse controls are Story 16.3 and must precede broad write capability.
