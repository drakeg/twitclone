# ADR-0042: Accessible errors and dynamic status

- Status: Accepted
- Date: 2026-08-22
- Sprint: 7
- Story: 7.2

## Context

Ripple displayed authentication failures as page-level flash messages without
associating them with invalid fields. Follow buttons changed visually after
asynchronous requests but did not expose toggle state or announce success and
failure. Search results also attached a second follow handler, risking duplicate
requests. Composer character and image-selection changes lacked a shared status
contract.

## Decision

- Render authentication failures as focused error summaries and connect each
  affected field with `aria-invalid` and `aria-describedby`.
- Preserve submitted username and email values after validation errors while
  never repopulating password fields.
- Use one page-level polite, atomic status region for asynchronous interaction
  results.
- Treat follow controls as toggle buttons with synchronized `aria-pressed`,
  visible text, action data, disabled in-flight state, and announced outcomes.
- Bind follow behavior once in the shared shell instead of per-template scripts.
- Expose the post character limit and image preview through named status
  relationships.
- Use assertive alert semantics for errors and warnings and polite status
  semantics for informational and successful flash messages.

## Consequences

- Keyboard and screen-reader users receive actionable error context and dynamic
  outcome feedback without route or validation-rule changes.
- Authentication templates now receive structured error and invalid-field
  context from their routes.
- Asynchronous failures leave the visible follow state unchanged and announce a
  retryable failure instead of failing silently.
- Manual screen-reader testing is still required; markup regression tests do not
  establish WCAG conformance.
