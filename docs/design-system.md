# Ripple visual system

Ripple uses familiar microblogging interaction patterns without reproducing
another product's brand or exact interface. The design favors readable content,
clear navigation, comfortable spacing, and obvious actions.

## Visual identity

- Warm off-white canvas and white content surfaces
- Deep ink text with muted secondary labels
- Violet primary actions with a coral supporting accent
- `Manrope` for display text and `DM Sans` for interface and body copy
- Rounded, softly elevated discovery and form surfaces
- A lightning-bolt conversation mark used by Ripple

Design tokens live as CSS custom properties at the top of
`static/css/styles.css`. New templates should use the existing variables and
component classes instead of introducing one-off colors and spacing.

## Layout

- Desktop: primary navigation, centered 640-pixel conversation column, and
  discovery rail
- Tablet: compact icon navigation with the conversation and discovery columns
- Mobile: single conversation column with a fixed bottom navigation bar

The centered feed remains the visual anchor at every width. Navigation and
discovery are supporting elements and must not compete with post content.

## Accessibility

- Keep the skip link and semantic navigation labels.
- Every icon-only action needs an accessible label.
- Preserve visible keyboard focus supplied by browser or component styles.
- Do not encode meaning using color alone.
- Respect reduced-motion preferences.
- Maintain form labels even when a visual placeholder is present.

## External assets

Bootstrap, Font Awesome, and Google Fonts are currently loaded from CDNs. The
interface falls back to system fonts, and core content remains usable without
icons or custom fonts. Self-hosting these assets can be considered in a later
performance and privacy pass.
