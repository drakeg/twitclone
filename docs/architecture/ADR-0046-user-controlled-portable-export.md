# ADR-0046: User-controlled portable export

## Status

Accepted.

## Context

Sprint 17 deferred broad federation while approving lower-risk interoperability foundations, including user-controlled account/data export. Ripple needs a provider-neutral export that gives a signed-in person useful copies of their identity and authored public work without introducing remote identity, delivery infrastructure, recurring cost, or claims of complete federation compatibility.

A first format must also avoid misleading users about its scope. Private communications, payment records, moderation records, analytics, and stored media bytes require separate privacy, security, and scale decisions.

## Decision

- Provide an authenticated, no-cost JSON download from `/profile/export.json`.
- Version the document independently from the public API as `ripple-portable-export` version 1.
- Include account profile fields, follower/following usernames, authored posts, Quotes, Replies, durable resources and revisions, and explicit space memberships.
- Include the requesting user's removed authored content with removal state so the export is not silently lossy.
- Exclude password hashes and other authentication secrets unconditionally.
- Explicitly list categories not included in version 1: private messages, billing records, moderation records, analytics, and media file bytes.
- Mark the response `private, no-store`, prevent content-type sniffing, and return it as an attachment.
- Keep export availability independent of paid plans, verification, popularity, or moderation authority.
- Do not emit or activate external webhooks as part of this local download.

## Consequences

- Users gain a practical portability baseline without new infrastructure or federation claims.
- Stable numeric identifiers and timestamps preserve useful relationships between root posts, Quotes, Replies, revisions, and spaces.
- Referenced content owned by another account is identified by relationship ID but is not copied into the export.
- Later versions may add separately reviewed private or operational categories while preserving the explicit version and scope contract.
