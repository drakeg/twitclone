# Sprint 32 — Space membership reporting and export

**Status:** Closeout implementation in progress.

## Goal

Give Space operators a useful portable membership report without exposing
private account data, introducing member ranking, or bypassing existing access
controls.

## Story 32.1 — Filtered roster CSV export

**Status:** Implemented; validation in progress.

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

## Story 32.2 — Spreadsheet-safe export refinement

**Status:** Implemented; validation in progress.

Harden the CSV workflow identified during Story 32.1 review:

- neutralize formula-leading usernames only in the exported representation so
  spreadsheet applications do not interpret user-controlled text as formulas;
- label and serialize join timestamps explicitly as UTC;
- mark authenticated roster downloads private/non-cacheable and disable MIME
  sniffing;
- preserve the stored username, roster UI, filters, ordering, privacy boundary,
  and stable filename.

These changes improve export safety without adding private-data fields,
ranking/scoring, or mutations.

## Story 32.3 — Sprint regression hardening

**Status:** Implemented; validation in progress.

Close the sprint with regression coverage for:

- exact-safe-maximum success and over-limit rejection;
- standards-compliant CSV escaping of user-controlled usernames;
- case-insensitive deterministic export ordering;
- invalid-role filter parity with the on-screen roster;
- no membership or membership-audit mutation;
- owner/moderator access to archived-Space reporting;
- spreadsheet neutralization for formula-leading and whitespace-prefixed
  formula-like usernames;
- the privacy, authorization, and no-ranking boundaries from Stories 32.1–32.2.

## Boundary

Sprint 32 exports operational membership facts only. It does not export email,
direct messages, moderation notes, private profile data, engagement scores, or
other sensitive account information.
