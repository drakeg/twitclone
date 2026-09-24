# ADR-0050: Import provenance before portable-data writes

## Status

Accepted.

## Context

Ripple now exports a versioned portability document, including authored content, visible messages, subscription metadata, entitlements, and owned-media references. Accepting that document back as writable application data creates materially different risks from exporting it.

A portable file can contain stale identifiers, references to other accounts, billing/access claims, removed content, and media references. Treating those fields as authoritative could create identity confusion, privilege escalation, forged relationships, or content whose source can no longer be explained.

## Decision

- Keep portable-data import execution disabled.
- Add a non-mutating compatibility contract for recognized `ripple-portable-export` version 4, version 5, and version 6 documents.
- Classify every exported collection as candidate, review-required, reference-only, dependency-blocked, or prohibited.
- Require persisted source provenance before any future record writes are enabled.
- Never allow portable data to grant subscriptions, entitlements, space roles, followers, or financial state.
- Do not recreate private messages from portable data without a separately reviewed multi-party semantics design.
- Do not fetch media references during compatibility assessment.
- Unknown fields are review signals, not trusted extensions.
- A structurally compatible document is not considered authorized for import.

## Consequences

- Ripple gains a testable import boundary without exposing a write endpoint.
- Future import development must preserve record origin rather than silently converting imported data into indistinguishable native records.
- Privilege and relationship state remain controlled by the destination system.
- Actual importing remains deferred until preview, authorization, provenance persistence, duplicate handling, rollback, limits, and moderation behavior are implemented.


## Portability version 5 compatibility

Sprint 22 advances the export document to version 5 to include `edited_at` for authored original posts. Version 4 remains structurally recognized by the non-mutating compatibility assessor so previously downloaded exports do not become immediately unreadable for future compatibility review.

This does not enable import execution. Version 5 adds lifecycle metadata only; all existing import prohibitions and provenance requirements remain unchanged.


## Portability version 6 compatibility

Sprint 22 version 6 adds a non-sensitive `removal_origin` field to lifecycle-bearing exported content. The value is limited to `owner`, `moderation`, `unknown`, or `null`; actor IDs and moderator identity are not exported.

Versions 4 and 5 remain recognized for non-mutating compatibility review. Import execution remains disabled, and removal-origin metadata does not grant any moderation or identity authority on a destination system.
