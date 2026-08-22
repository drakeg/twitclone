# ADR-0041: Accessibility interaction foundation

- Status: Accepted
- Date: 2026-08-21
- Sprint: 7
- Story: 7.1

## Context

Ripple's visual refresh introduced responsive navigation and a consistent
component system. It included a skip link and initial reduced-motion handling,
but keyboard focus, current-page state, decorative icon exposure, and dynamic
control state were not yet governed by one tested contract.

## Decision

- Keep a focusable main landmark as the target of the first-page skip link.
- Show a consistent high-contrast focus indicator only for focus-visible
  interactions, preserving pointer aesthetics without hiding keyboard focus.
- Expose current-page state in desktop and mobile navigation.
- Hide decorative navigation and composer icons when surrounding text or an
  accessible label already names the control.
- Keep the scheduler button's `aria-expanded` state synchronized with its
  controlled panel.
- Honor reduced-motion preferences for scrolling, transitions, and animations.
- Treat these rules as a regression-tested foundation, not a claim of WCAG
  conformance.

## Consequences

- Keyboard and assistive-technology users receive clearer location, focus, and
  control-state feedback without route or visual-layout changes.
- New interactive components must preserve visible focus and expose names,
  relationships, and state.
- Manual keyboard, zoom, contrast, and screen-reader review remains necessary;
  automated markup tests cannot establish conformance.
