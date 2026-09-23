# ADR-0050: Import provenance before portable-data writes

## Status

Accepted.

## Context

Ripple now exports a versioned portability document, including authored content, visible messages, subscription metadata, entitlements, and owned-media references. Accepting that document back as writable application data creates materially different risks from exporting it.

A portable file can contain stale identifiers, references to other accounts, billing/access claims, removed content, and media references. Treating those fields as authoritative could create identity confusion, privilege escalation, forged relationships, or content whose source can no longer be explained.

## Decision

- Keep portable-data import execution disabled.
- Add a non-mutating compatibility contract for recognized `ripple-portable-export` version 4 documents.
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
