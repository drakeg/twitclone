# ADR-0043: Semantic template audit

- Status: Accepted
- Date: 2026-08-22
- Sprint: 7
- Story: 7.3

## Context

The shared accessibility foundation and error/status work improved Ripple's
primary shell and authentication flows. A representative audit still found
secondary pages that began at heading level two, repeated images and icons that
added no meaning, data tables without explicit captions or header scope, and a
poll-choice control whose visible name was only a plus sign and whose dynamic
result was not announced.

## Decision

- Give each audited page one level-one heading and preserve a logical heading
  sequence below it.
- Treat adjacent repeated avatars and icons as decorative when visible text or
  an accessible control name already communicates their meaning.
- Make destructive message-control names identify the affected conversation.
- Give account plan and subscription tables concise captions and explicit
  column or row header scope.
- Name the poll choice control, focus each newly inserted choice, announce the
  result, and disable the control at its existing four-choice limit.
- Regression-test the core foreground/background token pairs against the WCAG
  2.x 4.5:1 threshold for normal text.

## Consequences

- Secondary account, discovery, messaging, and creation flows have clearer
  structure and less repetitive screen-reader output without layout changes.
- Dynamically added poll choices become immediately available to keyboard and
  screen-reader users.
- The contrast checks cover defined core token pairs, not every composited,
  browser-rendered, or third-party component state.
- Manual keyboard, zoom, high-contrast, and current screen-reader testing
  remains required; this decision does not claim WCAG conformance.
