# Accessibility

Ripple treats accessibility as an ongoing product requirement. This foundation
does not claim WCAG conformance; a complete audit with disabled users, assistive
technology, automated tools, and documented remediation is still required.
Automated checks cannot establish conformance on their own.

## Current interaction contract

- A keyboard-visible **Skip to content** link moves focus to the main landmark.
- Desktop and mobile navigation expose their purpose and current page.
- Interactive controls retain a high-contrast `:focus-visible` indicator.
- Icon-only controls have accessible names and decorative icons are hidden from
  assistive technology where the surrounding control already supplies a name.
- The post scheduler announces its controlled region and expanded state.
- Authentication errors move focus to a shared error summary, identify invalid
  fields, and preserve non-secret values for correction.
- Follow actions announce success or failure through one polite status region;
  toggle buttons expose their current pressed state.
- The composer exposes remaining characters and selected-image previews as
  status information.
- Audited secondary pages use one level-one heading, decorative repeated images
  stay out of the accessibility tree, and account data tables identify their
  purpose and header relationships.
- Dynamically added poll choices receive focus and a polite announcement; the
  add control exposes a descriptive name and its existing limit.
- Automated contrast regression checks cover Ripple's core text token pairs at
  the WCAG 2.x 4.5:1 normal-text threshold.
- Reduced-motion preferences disable smooth scrolling and transitions and
  minimize animations.

Do not remove these behaviors for visual consistency. Update the focused tests
when a deliberate interaction change requires a different accessible contract.

## Review checklist

Before releasing a UI change:

1. Navigate every changed flow keyboard-only, including reverse tab order.
2. Confirm focus is always visible and follows the visual/task order.
3. Confirm every control has a useful accessible name, state, and role.
4. Check headings and landmarks with a screen reader's navigation shortcuts.
5. Verify form labels, instructions, errors, and status updates are announced.
6. Check content at 200% browser zoom and narrow mobile widths without loss of
   actions or forced two-dimensional scrolling.
7. Enable reduced motion and confirm the flow works without essential animation.
8. Check meaningful images for useful alternatives and decorative images for
   empty alternatives.
9. Run automated accessibility checks, then manually verify their findings.

## Follow-up audit

The next accessibility stories should inventory every template, test color
contrast in all component states, audit form errors and dynamic announcements,
test representative flows with current screen readers, and document findings by
WCAG 2.2 success criterion and severity.
