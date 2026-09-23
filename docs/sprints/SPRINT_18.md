# Sprint 18 — User-Controlled Portability

**Status:** Completed.

## Goal

Continue the low-risk interoperability direction approved by Sprint 17 by giving people useful, understandable exports of their Ripple identity and authored work without activating federation or adding infrastructure spend.

## Story 18.1 — Portable public-content export

**Status:** Completed in PR #241.

- Add a free, authenticated JSON export with an explicit format name, version, timestamp, and scope.
- Include profile identity, social connections, authored posts, Quotes, Replies, durable resources/revisions, and explicit space memberships.
- Preserve the requesting user's removed authored records and their removal state.
- Exclude authentication secrets and prevent another account's referenced content from being copied into the export.
- Explain excluded version-1 categories in both the document and profile UI.
- Deliver the response as a private, non-cacheable attachment.

### Acceptance criteria

- Anonymous requests are redirected to login.
- The export is available without a paid entitlement or verification requirement.
- Password hashes and other accounts' authored content are absent.
- Quotes and Replies remain distinct record collections.
- Removed authored posts remain represented rather than silently disappearing.
- The profile editor provides a plainly labeled download control and scope explanation.
- Tests cover authentication, headers, stable shape, inclusion, isolation, secrets, and UI disclosure.

## Story 18.2 — Private-message portability boundary

**Status:** Completed in PR #244.

- Advance the portable document to version 2 and add direct messages still visible to the requester.
- Identify only direction and the other participant's username; do not export the other account's email, identity metadata, or internal account state.
- Exclude messages the requester deleted from their own view.
- Do not expose the other participant's deletion state or message-read state.
- Keep unrelated conversations excluded even when they involve a known participant.

### Acceptance criteria

- Sent and received messages still visible to the requester are exported in deterministic chronological order.
- Direction and participant username make each record understandable without copying another account profile.
- Requester-deleted messages and unrelated conversations are absent.
- Read state and either participant's deletion flags are absent.
- The profile UI explains that visible direct messages are included and requester-deleted messages are not.
- The version and omission list accurately describe the expanded format.

## Story 18.3 — Subscription and entitlement portability

**Status:** Completed in PR #245.

- Advance the portable document to version 3 with the requester's subscription and entitlement state.
- Export plan identity, current catalog amount, currency, interval, provider name, subscription status/period, and local timestamps.
- Label plan prices as current catalog amounts rather than claiming they are historical charges or receipts.
- Exclude provider customer/subscription identifiers, payment credentials, invoices, and charge receipts.
- Export only the requester's entitlement records and local subscription links.
- State explicitly that creator-support transactions are unavailable because Ripple does not process or persist them.

### Acceptance criteria

- Only the requesting account's subscriptions and entitlements are included.
- Provider name may be present, but opaque provider customer/subscription identifiers are absent.
- Current catalog price is clearly named and never represented as an amount charged.
- No payment credential, invoice, receipt, or another account's billing state is exposed.
- The export does not fabricate creator-support transaction history.
- UI and documentation accurately explain included records and omissions.

## Story 18.4 — Owned-media portability manifest

**Status:** Completed in PR #252.

- Advance the portable document to version 4 with a manifest of media references owned by the requester.
- Include the requester's profile-banner reference plus image/original-image references attached to the requester's own posts.
- Keep media bytes, signed URLs, storage credentials, and another account's media references out of the JSON document.
- State explicitly that the manifest is metadata only and does not guarantee that referenced media is still physically retained.
- Preserve deterministic ordering: profile banner first, then post image references by post ID, followed by original-image references by post ID.
- Add no archive generation, object-store reads, network fetches, or recurring infrastructure spend.

### Acceptance criteria

- The export format advances to version 4.
- Only media references owned through the requesting account's profile/posts appear.
- Another account's media reference is absent even when its post is referenced by a Quote or Reply.
- `packaged_bytes` is explicitly false and `media_file_bytes` remains in `not_included`.
- The profile UI explains the distinction between media references and packaged files.
- Tests cover manifest shape, ordering, account isolation, and the no-bytes boundary.

## Story 18.5 — Import mapping and provenance contract

**Status:** Completed in PR #253.

- Keep portable-data import execution disabled while defining a non-mutating compatibility contract.
- Recognize only the reviewed `ripple-portable-export` version 4 envelope.
- Classify each exported collection as candidate, review-required, reference-only, dependency-blocked, or prohibited.
- Require source provenance before any future imported record can be written.
- Prohibit portable data from granting space roles, follower relationships, subscriptions, entitlements, or financial state.
- Keep private-message import prohibited until multi-party identity/deletion semantics receive a separate design.
- Treat media references as opaque metadata and perform no filesystem, object-store, or network reads during assessment.
- Surface unknown fields for review instead of trusting or silently importing them.

### Acceptance criteria

- A compatibility assessor can identify recognized format/version documents without mutating application state.
- Import execution remains explicitly disabled.
- Billing, entitlements, private messages, and space memberships are classified as prohibited import sources.
- Quotes and Replies are blocked until their referenced records can be resolved safely.
- Media remains reference-only and cannot trigger arbitrary retrieval.
- Minimum provenance fields are documented and represented in code.
- Documentation defines duplicate, identity, relationship, authorization, rollback, moderation, and activation gates before any write endpoint is allowed.
- Tests cover compatibility, unsupported formats/versions, prohibited collections, reference-only media, unknown fields, and provenance requirements.

## Sprint outcome

Sprint 18 delivered a versioned, provider-neutral portability export through version 4 with explicit account-isolation and omission boundaries. The completed export covers account/profile data, social graph references, authored posts, Quotes, Replies, durable resources/revisions, explicit space memberships, direct messages still visible to the requester, subscription/entitlement state without provider secrets, and owned-media references without packaging media bytes.

The sprint also established the future-import boundary before any write capability exists. Import execution remains disabled; the compatibility assessor is non-mutating; privilege, billing, entitlement, private-message, and space-role state cannot be granted from portable data; and future imported records must preserve source provenance.

No Sprint 18 story activates federation, AWS infrastructure, paid services, remote media retrieval, or recurring spend.

## Deferred follow-up

- Evaluate packaged media only after archive size limits, storage/network cost, retention behavior, malware/file validation, and authorization are defined.
- Enable no import writes until a separate implementation story satisfies the Story 18.5 activation gate.
- Treat any future new export version as requiring a corresponding compatibility-contract review before import assessment recognizes it.

## Definition of done

Completed. Ripple provides a free authenticated portability export with explicit versioning, account isolation, sensitive-data exclusions, private-message and financial boundaries, a no-bytes owned-media manifest, and a documented/tested non-mutating import/provenance contract. Future import writes remain deliberately disabled.

## Story boundary

Story 18.1 is a local download, not ActivityPub federation, account migration, full backup, legal-compliance certification, or a promise that excluded private/operational data can never be exported. It adds no recurring service or cloud spend.
