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

**Status:** Implemented; CI validation pending.

Add role filtering and lightweight member profile cards while preserving opt-in
visibility and public-data-only boundaries.

## Story 36.3 — Directory regression hardening

**Status:** Planned.

Close the sprint with pagination, privacy default, search/filter parity,
archived-Space, account deletion, role changes, and no-private-data regression
coverage.
