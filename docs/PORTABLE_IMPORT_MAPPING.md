# Portable Import Mapping and Provenance Contract

Ripple does **not** currently import portable-export documents. This document defines the review boundary that must exist before any import endpoint, CLI write command, or background importer can be enabled.

## Current state

- Export format: `ripple-portable-export`
- Current reviewed source version: `4`
- Import execution: **disabled**
- Import assessment: non-mutating compatibility inspection only
- No account, content, relationship, billing, entitlement, or media records are created from an uploaded document.

## Collection mapping

| Source collection | Future disposition | Boundary |
| --- | --- | --- |
| `account` | Review required | Bio/theme-like profile fields may eventually map, but username and email identity must never be overwritten automatically. |
| `social_graph` | Reference only | Usernames can be previewed/resolved; no silent follow/follower creation. |
| `posts` | Candidate | Requires duplicate policy, timestamp policy, moderation handling, and persisted provenance before writes. |
| `quotes` | Blocked on dependency | Requires local mapping for the referenced root post and must not copy another account's content. |
| `replies` | Blocked on dependency | Requires root/parent resolution and preserved original authorship provenance. |
| `resources` | Candidate | Requires revision-order preservation, duplicate policy, and source-record provenance. |
| `space_memberships` | Prohibited | A portable file cannot grant membership or a role in a destination space. |
| `private_messages` | Prohibited | Other-party identity/content and deletion semantics make unilateral import unsafe. |
| `subscriptions` | Prohibited | Imported data cannot create or alter billing state. |
| `entitlements` | Prohibited | Imported data cannot grant paid, moderation, or administrative capabilities. |
| `creator_support_transactions` | Prohibited | Ripple will not trust financial claims supplied by a portable document. |
| `media_manifest` | Reference only | References may be inventoried, but import assessment must not fetch arbitrary paths/URLs. |

## Provenance requirements

Any future imported record must retain enough source information to distinguish imported data from native Ripple records and to support duplicate detection, rollback review, and user explanation.

Minimum provenance fields:

- `source_format`
- `source_version`
- `source_exported_at`
- `source_collection`
- `source_record_id`

A future implementation may add a destination import-batch ID, importer account ID, import timestamp, source checksum, and mapping status, but those additions do not replace the source identity fields above.

## Identity and relationship rules

Portable data is evidence supplied by the requesting user; it is not authority over another account.

Therefore a future importer must not:

- overwrite an existing username or email merely because the source document contains it;
- create followers on behalf of another account;
- recreate private messages as if authored or consented to by another participant;
- grant community/space roles;
- create subscriptions or entitlements;
- infer that an unresolved external username belongs to a similarly named Ripple account.

Any resolution of another account or referenced post must be explicit, reviewable, and fail closed when ambiguous.

## Content mapping rules

A future post/resource importer must define, before writes are enabled:

1. duplicate detection;
2. timestamp preservation vs destination creation time;
3. removed/moderated source-record handling;
4. reference resolution for Quotes and Replies;
5. topic and conversation-state mapping;
6. collision behavior for source IDs;
7. rollback/removal behavior for an import batch.

No source record should silently become ordinary native content with its origin erased.

## Media boundary

Version 4 exports only media references. Assessment must treat these as opaque metadata:

- no local filesystem traversal;
- no arbitrary URL retrieval;
- no object-store lookup;
- no signed URL generation;
- no assumption that the referenced media still exists.

Packaged-media import requires its own archive, file-type, size, malware, storage-cost, and ownership review.

## Compatibility behavior

The non-mutating assessor may report a document as structurally compatible while `import_enabled` remains false. Compatibility means only that the source format/version is recognized for review; it is **not** permission to write data.

Unknown collections or fields are surfaced for review rather than ignored as trusted input.

## Activation gate

An actual import capability requires a separate story and must include:

- explicit user confirmation;
- dry-run preview;
- per-collection mapping results;
- persisted import provenance;
- duplicate/idempotency behavior;
- authorization and account-isolation tests;
- limits on document size and record counts;
- transaction/rollback behavior;
- abuse and moderation review;
- no privilege, billing, or entitlement escalation from imported data.

Until those gates are implemented and reviewed, Ripple remains export-only.
