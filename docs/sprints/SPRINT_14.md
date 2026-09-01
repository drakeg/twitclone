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

**Status:** In implementation.

### Current implementation slice

- Replies support the same constructive labels as posts: **Helpful**, **Thoughtful**, and **Useful context**.
- Reply signals are stored in a dedicated `ReplyContribution` table rather than in post contribution history.
- Users may apply multiple distinct signal types to a reply, but cannot signal their own reply.
- Signals are toggleable and display transparent per-label counts; they do not alter thread ordering or feed ranking.
- Replies can be reported through the same Community Standards categories used for other public content.
- Reply reports use an isolated `ReplyReport` model so legacy `PostReport` constraints and IDs remain untouched.
- Reply reports appear in the shared admin moderation queue and can be filtered as content type **Reply**.
- Admin dismissal preserves the reply; removal hides the reply from the public thread and records moderator, time, and reason.
- All pending reports on the same reply are resolved together when an admin removes it.
- Migration `20260901_0033_reply_moderation.py` adds moderation metadata, reply contribution persistence, and reply-report persistence.

### Acceptance criteria

- Helpful/Thoughtful/Useful-context reply signals can be added and removed by authenticated non-authors.
- Self-signaling is blocked.
- Reply signals remain separate from post/topic reputation evidence and do not affect ordering.
- Authenticated non-authors can report a visible reply exactly once per account.
- Reply reports are attributable to reporter and author and appear in the existing admin moderation experience.
- Admins can dismiss a reply report without changing content visibility.
- Admin removal hides the reply, records the moderation decision, and resolves all pending reports for that reply.
- Removed replies do not render in the public thread or accept new contribution/report actions.
- Tests cover signal toggling, self-signal prevention, report deduplication, moderation queue visibility, dismissal, and removal.

### Story boundary

Story 14.4 integrates replies with constructive participation and Ripple-wide reporting/moderation. It does not make reply signals reputation/ranking inputs, add accepted answers, add user-authored reply deletion/editing, create reply-level appeals, or reinterpret historical Quotes.

## Story 14.5 — Reply integrity and compatibility

**Status:** Planned.

Close migration, deletion/removal, anti-abuse, accessibility, query/performance, and historical-Quote compatibility gaps before Sprint 14 completes.

## Definition of done

Sprint 14 is complete when Ripple has durable readable threaded replies with stable URLs, coherent conversation controls, appropriate contribution/moderation integration, and explicit compatibility boundaries that preserve Quote as a separate repost-with-comment action.
