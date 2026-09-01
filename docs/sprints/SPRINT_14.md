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

**Status:** In implementation.

### Current implementation slice

- The root post's conversation intent is now presented as the expectation for the entire reply thread rather than as decoration only on the root card.
- Top-level and nested reply forms repeat the root expectation so participants see it at the point of response.
- **Answered / resolved** remains informational and does not silently become a reply lock.
- Resolved conversations continue accepting top-level and nested replies unless the author also marks the conversation Closed.
- **Closed** remains the single conversation-health control that blocks new replies.
- A conversation may be both Resolved and Closed; the UI displays both states without conflating their semantics.
- Existing replies remain readable when Closed.
- Reply ordering, visibility, and Quote semantics are unchanged.

### Acceptance criteria

- Root conversation intent is visible as a thread-wide expectation.
- Reply controls present the same root expectation before a response is submitted.
- Resolved-only conversations remain replyable.
- Closed-only and Closed+Resolved conversations reject new top-level and nested replies.
- Existing descendants remain visible after closure.
- Both health states can be displayed simultaneously without contradictory copy.
- No paid status, verification, follower count, contribution total, or engagement velocity affects conversation-health behavior.
- Tests cover intent propagation, resolved replyability, combined Closed+Resolved state, existing-reply visibility, and top-level/nested blocking.

### Story boundary

Story 14.3 clarifies and regression-locks root-level intent and health semantics. It does not add reply-specific resolution markers, accepted-answer selection, per-reply intent, moderation controls, contribution signals, or ranking behavior.

## Story 14.4 — Reply contribution, reporting, and moderation

**Status:** Planned.

Extend constructive contribution signals and reporting/moderation controls to replies where semantics are well-defined, without converting them into popularity ranking inputs.

## Story 14.5 — Reply integrity and compatibility

**Status:** Planned.

Close migration, deletion/removal, anti-abuse, accessibility, query/performance, and historical-Quote compatibility gaps before Sprint 14 completes.

## Definition of done

Sprint 14 is complete when Ripple has durable readable threaded replies with stable URLs, coherent conversation controls, appropriate contribution/moderation integration, and explicit compatibility boundaries that preserve Quote as a separate repost-with-comment action.
