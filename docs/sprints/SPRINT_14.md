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

**Status:** In implementation.

### Current implementation slice

- Adds a dedicated `Reply` persistence model linked to the root post and reply author.
- Migration `20260901_0031_public_replies.py` advances from the current `0030` migration head.
- Public thread route: `/post/<tweet_id>/thread`.
- Stable reply permalink: `/post/<tweet_id>/reply/<reply_id>`.
- Authenticated users can publish a top-level public reply to an eligible root post.
- Replies render oldest-first with deterministic ID tie-breaking.
- Closing a conversation prevents new replies while preserving existing replies.
- Removed or future-scheduled root posts are unavailable through reply routes.
- Space-scoped posts are excluded from the global reply surface; space reply semantics require a separately scoped integration.
- Existing Quote rows are not imported, copied, or displayed as replies.
- Root authors receive an attributable notification when another user replies.

### Acceptance criteria

- A valid authenticated reply persists independently from Quote data.
- Every visible reply has a stable permalink.
- Thread rendering is deterministic and contains only eligible Reply records.
- Closed conversations reject new reply creation without hiding old replies.
- Space-scoped roots do not become reachable through global reply routes.
- Historical Quotes remain unchanged.
- Regression tests cover creation, permalinks, ordering, health controls, Quote separation, and space isolation.

### Story boundary

Story 14.1 establishes top-level replies only. Nested parent/child reply trees, reply-level contribution signals, reply moderation/reporting, deletion lifecycle, and richer thread navigation are intentionally deferred to later Sprint 14 stories.

## Story 14.2 — Threaded reply structure

**Status:** Planned.

Add explicit parent-reply relationships, readable nesting, stable ancestor/root navigation, and bounded presentation rules without engagement ranking.

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
