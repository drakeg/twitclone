# Sprint 22 — Lifecycle Contract Consistency

**Status:** In implementation.

## Goal

Keep Ripple's external and portable representations aligned with user-visible content lifecycle semantics so editing/removal state does not exist only in the browser UI.

## Story 22.1 — Propagate original-post edit state

**Status:** In implementation.

- Add nullable `edited_at` to the public API v1 post representation.
- Keep removed posts excluded from the public API exactly as before.
- Advance the provider-neutral portable export from version 4 to version 5.
- Include `edited_at` for authored original posts in portability v5.
- Keep removal metadata unchanged in portability output.
- Keep the non-mutating import assessor disabled for writes while recognizing both v4 and v5 documents.
- Preserve the decision not to expose previous post wording.
- Update tests and documentation for API and portability compatibility.

### Acceptance criteria

- Never-edited public posts expose `edited_at: null`.
- Edited public posts expose an ISO-8601 UTC `edited_at` value.
- API v1 still returns 404 for removed/non-public posts.
- Portable exports report version 5 and include post `edited_at`.
- Removed authored posts remain present in the owner's portability export with removal metadata.
- The import assessor accepts v4 and v5 for compatibility review but keeps `IMPORT_ENABLED = False`.
- No API edit/delete endpoint is introduced.
- No prior post wording is exposed.
- Regression tests cover API null/non-null edit state, export v5 metadata, and v4 backward compatibility.

## Planned follow-up stories

- Audit other mature lifecycle-bearing representations for consistency only where they already expose post state.
- Define whether author-removal provenance should appear in portable export beyond the existing non-sensitive removal reason/time contract.
- Avoid adding lifecycle fields to unrelated contracts solely for completeness.

## Boundary

Sprint 22 is contract-alignment work. It does not enable portable imports, API editing/deletion, physical erasure, new infrastructure, or paid services.
