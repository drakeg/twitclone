# Sprint 32 — Space membership reporting and export

**Status:** In progress.

## Goal

Give Space operators a useful portable membership report without exposing
private account data, introducing member ranking, or bypassing existing access
controls.

## Story 32.1 — Filtered roster CSV export

**Status:** In progress.

Add an operator-only CSV export that uses the same username search and role
filter semantics as the on-screen member roster.

### Acceptance criteria

- Only Space owners and moderators can export the roster.
- The export accepts the same case-insensitive username search and
  owner/moderator/member role filters as the roster.
- Exported fields are limited to public username, Space role, and joined-at
  timestamp; email and other private account data are excluded.
- Ordering is deterministic and matches the roster's alphabetical semantics.
- Export size is explicitly capped to a documented safe maximum rather than
  loading an unbounded membership table into memory.
- The filename is stable and derived from the Space slug.
- CSV output uses a standard content type and safe attachment disposition.
- Exporting does not mutate membership, audit, ranking, reputation,
  verification, or paid status.
- Archived Spaces remain exportable to authorized operators because reporting
  is read-only.

## Story 32.2 — Export usability refinement

**Status:** Planned after Story 32.1 is exercised.

Use implementation/testing gaps to improve operator reporting without adding
private-data export or ranking/scoring.

## Story 32.3 — Sprint regression hardening

**Status:** Planned.

Close the sprint with authorization, filter parity, escaping, size-bound,
archived-Space, and privacy regression coverage.

## Boundary

Sprint 32 exports operational membership facts only. It does not export email,
direct messages, moderation notes, private profile data, engagement scores, or
other sensitive account information.
