# Sprint 22 — Lifecycle Contract Consistency

**Status:** Completed.

## Goal

Keep Ripple's external and portable representations aligned with user-visible content lifecycle semantics so editing/removal state does not exist only in the browser UI.

## Story 22.1 — Propagate original-post edit state

**Status:** Completed in PR #271.

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

## Story 22.2 — Non-sensitive removal origin in portability

**Status:** Completed in PR #272.

- Advance the portable export from version 5 to version 6 rather than silently mutating the already-merged v5 schema.
- Add `removal_origin` to exported authored posts, quotes, replies, and resources that already expose removal state.
- Use only the neutral values `owner`, `moderation`, `unknown`, or `null`.
- Derive the value internally from ownership/removal metadata without exporting `removed_by_id`, moderator usernames, or other moderator identity.
- Keep existing `is_removed`, `removed_at`, and `removal_reason` fields unchanged.
- Preserve v4 and v5 recognition in the non-mutating import compatibility assessor while adding v6.
- Keep import execution disabled.

### Acceptance criteria

- Visible/non-removed content exports `removal_origin: null`.
- Content removed by its owner exports `removal_origin: owner`.
- Content removed by a different authorized actor exports `removal_origin: moderation`.
- Legacy removed content without actor metadata exports `removal_origin: unknown`.
- `removed_by_id` and moderator identity are absent from the export.
- Portable export version is 6.
- The import assessor accepts v4, v5, and v6 for compatibility review and remains non-mutating.
- Tests cover all four origin values plus identity non-disclosure.

## Story 22.3 — External lifecycle representation audit

**Status:** Completed by audit in this closeout.

The mature external representations now have consistent lifecycle semantics:

- Public API v1 exposes nullable `edited_at` for public original posts.
- Removed/non-public posts remain unavailable through the public API.
- Portable export v6 includes authored post edit state plus removal time, reason, and non-sensitive removal origin.
- Portability compatibility review recognizes v4, v5, and v6 while import execution remains disabled.

No additional lifecycle fields are being added to unrelated internal views, analytics, or contracts solely for symmetry. Future additions require an existing consumer contract or a concrete product/compliance need.

## Sprint outcome

Sprint 22 aligned Ripple's mature public and portable representations with the author-controlled lifecycle introduced in Sprint 21. Edit state is now visible consistently to API consumers and export owners, portability schema evolution remains explicit and backward-recognizable, and removal provenance is useful without exposing moderator identity.

## Definition of done

Completed. External lifecycle contracts are aligned, removed-content visibility boundaries remain intact, portable imports remain disabled, and the sprint stops before speculative field propagation into unrelated surfaces.

## Boundary

Sprint 22 is contract-alignment work. It does not enable portable imports, API editing/deletion, physical erasure, new infrastructure, or paid services.
