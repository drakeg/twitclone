# ADR-0019: Timeline page-number pagination

- Status: Accepted
- Date: 2026-08-12
- Sprint: 3
- Story: 3.4

## Context

The timeline currently renders every visible Tweet, Retweet, Quote, and Poll in
one response. Stories 3.2 and 3.3 established a normalized item contract, fixed
scheduled visibility, and a deterministic ordering tuple that pagination must
preserve.

The content types still live in separate tables. Introducing database-level
cross-model cursor pagination now would combine a public navigation change with
a larger query redesign.

## Decision

Add page-number pagination after normalized timeline assembly and ordering:

- 20 items per page;
- `page=1` by default;
- invalid, missing, zero, and negative values resolve to page 1;
- values beyond the final page resolve to the final page;
- an empty timeline is page 1 of 1; and
- previous and next controls appear only when multiple pages exist.

The pagination result exposes items, current page, page size, total item count,
total page count, and previous/next navigation state. Slicing occurs only after
the Story 3.3 ordering tuple has been applied, preventing gaps or duplicates at
equal timestamps.

## Consequences

### Positive

- Timeline responses have a bounded number of rendered items.
- Navigation is predictable and works with ordinary links.
- Ordering and scheduled visibility remain unchanged.
- The pagination contract is independently tested and reusable.

### Negative

- All visible timeline rows are still assembled before the requested page is
  sliced.
- Page-number pagination can shift when new activity is added between requests.
- Database-level cursor pagination remains future optimization work.

## Guardrails

- A query-performance rewrite must preserve page size, ordering, visibility, and
  navigation behavior unless intentionally versioned.
- New filters or URL parameters must be retained in pagination links.
- Scheduling, ownership, and interaction rules remain separate stories.
