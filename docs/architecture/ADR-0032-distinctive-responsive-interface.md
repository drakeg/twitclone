# ADR-0032: Distinctive responsive interface

- Status: Accepted
- Date: 2026-08-16
- Sprint: Priority design sprint

## Context

Ripple used an almost unmodified Bootstrap navbar, generic cards, and a
two-column grid. The custom stylesheet was stored under `static/css` while the
base template requested it from the static root, so its limited rules were not
reliably loaded. The interface did not establish a recognizable identity or
adapt its navigation meaningfully for small screens.

## Decision

- Introduce a Ripple-owned design system with reusable CSS tokens.
- Use a three-column desktop shell, compact tablet navigation, and bottom mobile
  navigation around a consistent centered conversation column.
- Refresh the timeline, composer, profile, authentication, discovery, forms,
  lists, and empty states without changing application behavior.
- Use a violet/coral identity and lightning mark rather than copying another
  microblogging product's colors, logo, or exact components.
- Keep Bootstrap as a transitional utility dependency while package-owned CSS
  defines the visible design.

## Consequences

- Existing workflows receive a substantial visual improvement without backend
  or database changes.
- Templates have clearer semantic landmarks and accessible icon labels.
- CDN-hosted fonts and icons remain an availability and privacy tradeoff.
- Future UI changes should extend the documented system instead of adding
  isolated Bootstrap styling.

## Guardrails

- Preserve all existing routes, form field names, CSRF handling, and actions.
- Validate desktop and mobile layouts before merging visual changes.
- Do not copy proprietary branding or reproduce another interface pixel for pixel.
