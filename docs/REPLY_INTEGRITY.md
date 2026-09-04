# Reply Integrity and Compatibility

Sprint 14 establishes public Replies as a durable conversation primitive that remains separate from Quote posts.

## Persistence and compatibility

- Replies use the dedicated `reply` persistence model and stable reply/thread URLs.
- Historical Quotes remain Quote records. They are not copied, migrated, counted, or rendered as Replies.
- Story 14.5 does not require a schema migration; it hardens behavior on top of migrations `0031` through `0033`.
- Removed root posts remain unavailable through the global reply surface, and space-scoped posts remain isolated from global reply endpoints.

## Removal semantics

Moderation removal hides the removed Reply itself. Visible descendants are preserved rather than cascade-hidden as a presentation side effect.

When a visible Reply references a removed parent:

- the child remains readable;
- the removed parent's body and author identity are not rendered through the child;
- Ripple shows a neutral **Replying to a removed reply** tombstone;
- no public permalink to the removed parent is emitted.

This keeps moderation removal from creating broken thread links or leaking removed-parent context.

## Nesting and anti-abuse

Persistent reply nesting is capped at 12 levels. The cap is enforced server-side when a nested Reply is created, not only hidden in the UI.

The visual indentation cap remains three levels. Deeper valid hierarchy is preserved in storage and communicated as a deeper thread without allowing unbounded horizontal layout.

The thread assembler also guards parent traversal against malformed or cyclic parent chains so a corrupt chain cannot recurse indefinitely during presentation.

## Query behavior

Thread assembly loads the thread's Reply records in one ordered query and loads constructive Reply contributions in one bulk query for the visible reply IDs. Contribution counts are then assembled in memory.

This replaces per-Reply lazy contribution lookups in the thread-building path and prevents contribution rendering from growing into an N+1 query pattern as a conversation grows.

## Accessibility

Interactive Helpful, Thoughtful, and Useful context controls expose `aria-pressed` state and an accessible label including the signal name and current total when present.

Removed-parent context is expressed as readable text rather than a dead link.

## Ranking and product boundaries

Reply ordering remains deterministic and relationship-independent. Story 14.5 does not use contribution totals, reports, follower counts, verification, subscriptions, paid entitlement, or inferred traits to reorder Replies.

No accepted-answer ranking, automatic collapse, engagement optimization, or historical Quote conversion is introduced by this integrity pass.
