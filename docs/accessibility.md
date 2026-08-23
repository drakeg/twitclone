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
- Narrow viewport and heavy-zoom safeguards allow headers/actions to wrap,
  collapse the two-column scheduling controls to one column, wrap long content,
  and preserve horizontal scrolling only for genuinely tabular data.

Do not remove these behaviors for visual consistency. Update the focused tests
when a deliberate interaction change requires a different accessible contract.

## Story 7.4 audit record

Story 7.4 extends the static and interaction audit toward the representative
assistive-technology and reflow checks required by the Sprint 7 goal. The code
changes in this story are intentionally limited to findings that can be
verified from repository structure and deterministic browser behavior.

| WCAG 2.2 area | Current evidence | Story 7.4 disposition |
| --- | --- | --- |
| 1.3.1 Info and Relationships | landmarks, heading hierarchy, form labels/legends, table captions and scoped headers | retained and regression-tested |
| 1.4.3 Contrast (Minimum) | automated checks for core text tokens | retained; automated checks do not cover every rendered component state |
| 1.4.10 Reflow | responsive shell plus Story 7.4 wrapping/single-column safeguards | improved; manual 320 CSS-pixel / 400% browser verification remains required before any conformance claim |
| 2.1.1 Keyboard | skip link, visible focus, native controls, dynamic poll focus | retained; representative manual keyboard walkthrough remains part of release review |
| 2.4.3 Focus Order | DOM order follows visual/task order in audited templates | no automated conformance claim; verify manually after layout changes |
| 2.4.7 Focus Visible | shared high-contrast `:focus-visible` rule | regression-tested |
| 3.3.1 Error Identification | authentication error summary and invalid-field relationships | regression-tested |
| 4.1.2 Name, Role, Value | named icon controls, follow toggle state, scheduler expanded state | expanded by hiding decorative timeline/action icons from assistive technology |
| 4.1.3 Status Messages | follow/composer/poll status regions | regression-tested |

### Manual assistive-technology gate

Repository tests cannot substitute for a real screen reader. Before Ripple can
claim that Sprint 7 has verified a representative assistive-technology flow,
perform and record at least the following against a release candidate:

1. NVDA + current Firefox or Chrome on Windows: sign in, navigate the timeline,
   create a post, follow/unfollow a user, open notifications, and send/read a
   message.
2. VoiceOver + current Safari on macOS: repeat the timeline, profile-editing,
   messaging, and moderation/admin flows available to the test account.
3. At 200% and 400% browser zoom, verify the same representative flows without
   clipped controls, lost content, or two-dimensional page scrolling. Data
   tables may use their intentional local horizontal scroll container.
4. Record browser, assistive-technology version, viewport/zoom, result, defect
   reference, and retest result. Do not place private account data in the repo.

Until that evidence exists, Ripple should continue to describe accessibility as
an actively tested product requirement rather than claim WCAG conformance.

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

Remaining accessibility work should complete and archive the manual assistive-
technology gate above, broaden component-state contrast review, and remediate
findings by WCAG 2.2 success criterion and severity. Automated results alone
must never be presented as proof of conformance.
