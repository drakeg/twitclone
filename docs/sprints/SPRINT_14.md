# Sprint 14 — Replies and Conversation Structure

**Status:** Completed.

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

**Status:** Completed.

- Nested Reply creation is capped at 12 persisted levels and enforced server-side.
- Visual indentation remains bounded while deeper valid hierarchy stays persisted and readable.
- Parent traversal guards against malformed/cyclic chains.
- Thread assembly bulk-loads constructive Reply contributions instead of querying per Reply.
- Visible descendants of a removed parent remain readable through a neutral tombstone without exposing removed content, identity, or a dead permalink.
- Helpful/Thoughtful/Useful-context controls expose pressed/unpressed accessibility state.
- `docs/REPLY_INTEGRITY.md` records persistence, anti-abuse, removal, performance, accessibility, ranking, and compatibility boundaries.
- Historical Quotes remain Quote records and are never reclassified as Replies.
- Story 14.5 merged in PR #218.

## Sprint outcome

Sprint 14 delivered durable, readable threaded replies with stable URLs, coherent conversation intent/health behavior, reply-level constructive contribution and moderation integration, bounded deep-thread handling, removal-safe descendants, accessibility state, and explicit compatibility boundaries preserving Quote as a separate repost-with-comment action.
