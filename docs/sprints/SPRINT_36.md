# Sprint 36 — Space member directory and privacy

**Status:** In progress.

## Goal

Give current Space members a useful people directory while treating Space
membership association as private by default and exposing only public profile
fields after explicit member opt-in.

## Story 36.1 — Opt-in member directory

**Status:** Implemented; validation in progress.

Add a member-only searchable directory backed by a per-Space membership privacy
preference.

### Acceptance criteria

- Directory access requires current Space membership.
- New memberships are hidden from the directory by default.
- Each member controls only their own directory visibility; operators cannot
  silently opt another member in.
- Opted-in rows expose public username, public bio, and Space role only.
- Email, account identifiers, verification internals, paid status, moderation
  history, ranking/reputation data, and private profile data are excluded.
- Directory search is case-insensitive and ordering is deterministic/alphabetical.
- Results are paginated at 25 rows.
- Archived Spaces keep directory reads and personal opt-in/opt-out available
  because those actions are privacy/read-state operations, not new participation.
- Schema change is reversible.

## Story 36.2 — Directory usability

**Status:** Implemented; validation in progress.

Add role filtering and clearer public-profile cards while preserving opt-in
visibility and public-data-only boundaries.

### Acceptance criteria

- Members can combine case-insensitive username search with owner/moderator/member
  role filters.
- Invalid role values fall back safely to all roles rather than broadening data
  beyond opted-in memberships.
- Pagination preserves active search and role filters.
- Directory cards link clearly to the existing public profile and show only
  username, public bio, and Space role.
- Opt-out rows remain excluded regardless of filters.

## Story 36.3 — Directory regression hardening

**Status:** Ready after Story 36.2 validation.

Close the sprint with pagination, privacy default, search/filter parity,
archived-Space, account deletion, role changes, and no-private-data regression
coverage.
