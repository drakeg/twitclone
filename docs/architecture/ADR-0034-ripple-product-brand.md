# ADR-0034: Ripple product brand

- Status: Accepted
- Date: 2026-08-16

## Context

The application began as a Twitter-style learning project and retained the
working name TwitClone after its functionality and visual identity grew beyond
a simple clone.

## Decision

The user-facing product name is **Ripple**. Templates, page titles, navigation,
search and discovery copy, project documentation, and accessible branding use
Ripple.

The GitHub repository name and internal Python package remain `twitclone` for
now. Renaming that namespace would require a broad import, deployment, and
operational refactor without improving the user experience, so it is explicitly
outside this branding change.

## Consequences

- Users see one consistent Ripple identity throughout the application.
- Existing imports, deployment commands, migrations, and repository links remain
  stable.
- A future internal namespace rename can be handled as a separate technical
  migration if it provides enough value to justify the risk.
