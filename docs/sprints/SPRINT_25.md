# Sprint 25 — Accessibility Evidence Capture

**Status:** Completed.

## Goal

Make Ripple's remaining manual accessibility release gate reproducible and reviewable without turning automated record validation into a conformance claim.

## Story 25.1 — Sanitized manual evidence record

**Status:** Completed in PR #297.

- Add a repository-safe example record covering the documented NVDA, VoiceOver, and 200%/400% zoom scenarios.
- Require an exact release SHA, review date, operator/reference, browser/AT versions, viewport, result, defect reference when blocked/failed, and optional retest result.
- Keep real completed evidence outside the public repository.

## Story 25.2 — Offline evidence validator

**Status:** Completed in PR #297.

- Validate the record format/version and exact required scenario set.
- Fail closed on malformed release identity, missing scenarios, invalid browser/AT combinations, incomplete defect references, or placeholder data in an approved record.
- Permit structurally valid blocked records so incomplete evidence can still be archived/reviewed accurately.
- Never set `RIPPLE_ACCESSIBILITY_EVIDENCE_PASSED` or treat validation as launch authorization.

### Acceptance criteria

- The repository example validates structurally while remaining explicitly blocked.
- Approved records require all required scenarios to have an effective pass result and no template placeholders.
- NVDA scenarios require Windows plus Firefox or Chrome; VoiceOver scenarios require macOS plus Safari.
- 200% and 400% zoom scenarios are both mandatory.
- Failed/blocked scenarios require a defect reference.
- Validation supports human-readable and machine-readable output.
- Automated tests prove the validator cannot substitute for the separate launch-gate acknowledgment.

## Boundary

This sprint records and validates manual evidence only. It does not perform screen-reader testing, claim WCAG conformance, provision infrastructure, enable AWS, or authorize public launch.

## Sprint outcome

Sprint 25 delivered a sanitized accessibility evidence template, an offline validator, and regression coverage for Ripple's documented NVDA, VoiceOver, and 200%/400% zoom review matrix. The tooling validates evidence structure and completeness while deliberately refusing to perform the manual tests, set the launch-gate flag, claim WCAG conformance, or authorize release.

The remaining work is operational evidence collection against a release candidate. That manual activity remains a cross-cutting launch gate rather than additional Sprint 25 implementation.

## Definition of done

Completed. The repository now provides a reproducible, reviewable way to record and validate manual accessibility evidence without converting automation into a conformance claim.
