# Sprint 14 — Replies and Conversation Structure

**Status:** In implementation.

## Goal

Add a true public reply model so Ripple conversations can develop as readable discussions instead of relying on Quote as the only public response mechanism.

## Product principles

- Replies and Quotes remain distinct actions with distinct semantics.
- Historical Quotes are never silently reclassified as replies.
- Conversation intent and author health controls apply consistently to the reply surface.
- Stable URLs and explicit visibility rules precede deeper threading or ranking.
- Removed, scheduled, or space-scoped source content must not leak through a global reply endpoint.
- Reply ordering is deterministic and not engagement-ranked.

## Story 14.1 — Persistent public reply foundation

**Status:** Completed.

- Added the dedicated persistent `Reply` model and migration `20260901_0031_public_replies.py`.
- Added `/post/<tweet_id>/thread` and stable reply permalinks.
- Added authenticated top-level public replies ordered oldest-first with deterministic ID tie-breaking.
- Closed conversations preserve existing replies while rejecting new replies.
- Removed, scheduled, and space-scoped root posts are excluded from the global reply surface.
- Historical Quotes remain separate and unchanged.
- Story 14.1 merged in PR #211.

## Story 14.2 — Threaded reply structure

**Status:** In implementation.

### Current implementation slice

- Adds nullable `parent_reply_id` to `Reply`, preserving top-level replies while allowing explicit parent/child relationships.
- Migration `20260901_0032_threaded_replies.py` advances from `0031` and uses Alembic batch alteration for SQLite compatibility.
- Adds a nested reply POST route scoped by both root post and parent reply.
- Parent replies must belong to the same root post and remain publicly visible.
- Thread rendering is deterministic depth-first: root replies and each sibling group are ordered oldest-first with ID tie-breaking.
- Each nested reply displays an attributable parent link using the parent's stable permalink.
- Reply permalinks continue to anchor into the full root conversation so ancestor/root context is not lost.
- Visual indentation is capped at three levels; deeper hierarchy remains intact in persistence and navigation and is labeled as a deeper thread.
- Closed conversations reject nested replies using the same root conversation health boundary as top-level replies.
- Nested reply notifications target the parent reply author when appropriate rather than always notifying only the root author.

### Acceptance criteria

- Nested replies persist an explicit parent relationship without changing Quote semantics.
- A parent reply from a different root cannot be used to create a cross-root child.
- Thread rendering preserves deterministic parent-before-child depth-first order.
- Every nested reply and parent remains reachable through stable reply permalinks.
- Deep conversations preserve their actual hierarchy while visual indentation remains bounded.
- Closed conversations prevent new top-level and nested replies without hiding existing descendants.
- No follower count, contribution total, paid status, verification state, or engagement velocity changes reply ordering.
- Tests cover nested persistence, cross-root rejection, ordering, parent navigation, depth bounds, and closed-conversation behavior.

### Story boundary

Story 14.2 adds structural nesting only. Reply-level contribution signals, reporting/moderation, reply removal lifecycle, resolved/answered descendant semantics, and broader anti-abuse/performance work remain later Sprint 14 stories.

## Story 14.3 — Conversation intent and health semantics

**Status:** Planned.

Apply root conversation intent, Closed, and Answered/Resolved semantics coherently throughout nested replies and clarify author/replier expectations in the UI.

## Story 14.4 — Reply contribution, reporting, and moderation

**Status:** Planned.

Extend constructive contribution signals and reporting/moderation controls to replies where semantics are well-defined, without converting them into popularity ranking inputs.

## Story 14.5 — Reply integrity and compatibility

**Status:** Planned.

Close migration, deletion/removal, anti-abuse, accessibility, query/performance, and historical-Quote compatibility gaps before Sprint 14 completes.

## Definition of done

Sprint 14 is complete when Ripple has durable readable threaded replies with stable URLs, coherent conversation controls, appropriate contribution/moderation integration, and explicit compatibility boundaries that preserve Quote as a separate repost-with-comment action.
