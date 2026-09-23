# ADR-0049: Portable media manifest without file packaging

## Status

Accepted.

## Context

Ripple's portable export already exposes authored post image references and the requester's profile-banner reference in account data, but it does not provide one explicit inventory of owned media. Packaging media bytes would introduce archive-size, retention, authorization, object-store access, and potentially network-cost decisions that are not yet defined.

A reference manifest can improve portability without pretending to be a backup or requiring Ripple to retrieve media during export.

## Decision

- Advance `ripple-portable-export` to version 4.
- Add a `media_manifest` containing only references owned through the requesting account's profile and authored posts.
- Emit the profile banner first when present, followed by post image references and original-image references in deterministic post order.
- Mark `packaged_bytes` as `false`.
- Do not emit media bytes, signed download URLs, storage credentials, bucket details, or media references owned only by another account.
- Do not perform object-store reads or remote fetches while building the JSON export.
- Continue listing `media_file_bytes` as excluded.
- Treat references as descriptive metadata, not proof that an object is still retained or retrievable.

## Consequences

- Users receive a clearer inventory of which media references belong to their exported Ripple content.
- Export generation remains local/database-bound and adds no storage or network cost.
- The export remains unsuitable as a full media backup.
- A future packaged-media capability requires explicit archive limits, storage/network cost review, retention semantics, and authorization tests before implementation.
