# Sprint 18 — User-Controlled Portability

**Status:** In implementation.

## Goal

Continue the low-risk interoperability direction approved by Sprint 17 by giving people useful, understandable exports of their Ripple identity and authored work without activating federation or adding infrastructure spend.

## Story 18.1 — Portable public-content export

**Status:** Completed in this branch.

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

## Planned follow-up stories

- Evaluate export of private communications with participant privacy and redaction rules.
- Evaluate billing and support-transaction portability with financial-data handling requirements.
- Add media manifests or packaged media only after size limits, storage cost, and authorization are defined.
- Document import mappings and provenance before accepting any portable data back into Ripple.

## Story boundary

Story 18.1 is a local download, not ActivityPub federation, account migration, full backup, legal-compliance certification, or a promise that excluded private/operational data can never be exported. It adds no recurring service or cloud spend.
