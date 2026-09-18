# Sprint 18 — User-Controlled Portability

**Status:** In implementation.

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

**Status:** Completed in this branch.

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

## Planned follow-up stories

- Add media manifests or packaged media only after size limits, storage cost, and authorization are defined.
- Document import mappings and provenance before accepting any portable data back into Ripple.

## Story boundary

Story 18.1 is a local download, not ActivityPub federation, account migration, full backup, legal-compliance certification, or a promise that excluded private/operational data can never be exported. It adds no recurring service or cloud spend.
