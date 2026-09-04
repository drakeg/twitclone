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

**Status:** Completed.

- Added nullable `parent_reply_id` and migration `20260901_0032_threaded_replies.py`.
- Added nested replies scoped to the same root post.
- Added deterministic parent-before-child depth-first rendering.
- Preserved stable reply permalinks and explicit parent navigation.
- Capped visual indentation while preserving deeper persisted hierarchy.
- Applied Closed behavior consistently to top-level and nested replies.
- Story 14.2 merged in PR #212.

## Story 14.3 — Conversation intent and health semantics

**Status:** Completed.

- Root conversation intent is presented as the expectation for the entire reply thread and repeated at reply controls.
- **Answered / resolved** remains informational and does not lock replies.
- **Closed** remains the only root health state that blocks new top-level and nested replies.
- Closed and Resolved can coexist without conflating their meaning.
- Existing replies remain readable after closure.
- Story 14.3 merged in PR #213.

## Story 14.4 — Reply contribution, reporting, and moderation

**Status:** Completed.

- Replies support **Helpful**, **Thoughtful**, and **Useful context** signals in dedicated Reply contribution persistence.
- Self-signaling is blocked; signals are reversible and do not alter ordering or topic reputation.
- Replies can be reported through Community Standards categories using the dedicated `ReplyReport` model.
- Reply reports appear in the shared admin moderation queue with Reply filtering.
- Admin dismissal preserves the Reply; admin removal hides it and records moderator, time, and reason.
- Pending reports for a removed Reply are resolved together.
- Migration `20260901_0033_reply_moderation.py` added moderation metadata, Reply contribution persistence, and Reply-report persistence.
- Story 14.4 merged in PR #214.

## Story 14.5 — Reply integrity and compatibility

**Status:** In implementation.

### Current implementation slice

- Nested Reply creation is capped at 12 persisted levels and enforced server-side.
- Existing three-level visual indentation remains bounded while deeper valid hierarchy stays persisted and understandable.
- Thread parent traversal guards against malformed/cyclic parent chains rather than recursing indefinitely.
- Thread assembly bulk-loads constructive Reply contributions instead of issuing a lazy contribution lookup for each Reply.
- A visible child of a removed parent remains readable but renders a neutral **Replying to a removed reply** tombstone.
- Removed-parent body, identity, and dead permalink are not exposed through surviving descendants.
- Helpful/Thoughtful/Useful-context toggle buttons expose `aria-pressed` state and accessible labels.
- Regression coverage verifies the depth cap, removed-parent presentation, accessible signal state, and historical Quote separation.
- `docs/REPLY_INTEGRITY.md` records persistence, anti-abuse, removal, performance, accessibility, ranking, and compatibility boundaries.
- No schema migration is required for Story 14.5.

### Acceptance criteria

- A nested Reply cannot be created beyond the documented server-side depth cap.
- Valid deep threads remain readable without unbounded horizontal indentation.
- Malformed/cyclic parent relationships cannot cause unbounded presentation traversal.
- Reply contribution display does not require a per-Reply contribution query.
- Removing a parent does not silently remove visible descendants or expose the removed parent's content/identity through them.
- Interactive contribution signals expose understandable pressed/unpressed accessibility state.
- Historical Quotes remain Quote records and never appear as Reply thread rows unless a separate real Reply also exists.
- Story 14.5 changes do not introduce contribution/engagement ranking, accepted-answer ranking, paid reach, or inferred-trait behavior.

### Product boundary

This integrity pass closes threading, removal, accessibility, query, and compatibility gaps. It does not add user-authored Reply editing/deletion, accepted answers, engagement-based collapse/ranking, reply-level appeals, or historical Quote migration.

## Definition of done

Sprint 14 is complete when Ripple has durable readable threaded replies with stable URLs, coherent conversation controls, appropriate contribution/moderation integration, and explicit compatibility boundaries that preserve Quote as a separate repost-with-comment action.
