# Sprint 13 — Communities and Topic Spaces

**Status:** In implementation.

## Goal

Create persistent spaces where conversations, resources, and topic contribution history can coexist without weakening Ripple's global Community Standards or turning community membership into a ranking signal.

## Product principles

- Membership is explicit; Ripple does not infer community membership from browsing, location, ideology, or other sensitive traits.
- Community membership, ownership, or moderation roles do not purchase or imply global reach, reputation, verification, or paid status.
- Global Community Standards remain authoritative inside every space.
- Roles and moderation powers must be understandable and auditable before additional privileges are introduced.
- Current Sprint 13 spaces are public. Private/local coordination requires separately defined privacy and location boundaries.

## Story 13.1 — Persistent space and membership foundation

**Status:** Completed.

- Persistent public spaces have stable normalized slugs, names, descriptions, owners, and creation timestamps.
- Explicit membership records establish current space roles and one membership per user/space.
- Creators become owners atomically; signed-in users can explicitly join and leave public spaces.
- `/spaces/`, `/spaces/create`, and `/spaces/<slug>` provide public discovery and stable space identity.
- Membership has no effect on feed ranking, global reputation, paid entitlement, or verification.
- Story 13.1 merged in PR #201.

## Story 13.2 — Space-specific conversations

**Status:** Completed.

- `SpacePost` links an existing durable `Tweet` to exactly one space.
- Only explicit members can publish into a space; public visitors can read current public-space conversations.
- Space conversations are deterministic newest-first and clearly labeled as space-scoped.
- Space-scoped posts, plus reposts/quotes referencing them, are excluded from global feeds.
- Story 13.2 merged in PR #202.

## Story 13.3 — Space resources and knowledge

**Status:** Completed.

- `SpaceResource` associates an existing durable resource with a public space without copying it.
- Every association records who explicitly linked it and when.
- Removed resources are excluded from space knowledge and cannot be newly linked.
- Link recency is browsing order only and does not change global placement or reputation.
- Story 13.3 merged in PR #205.

## Story 13.4 — Roles and moderation boundaries

**Status:** Completed.

- Explicit roles are `owner`, `moderator`, and `member`.
- Only owners can grant or revoke moderator role.
- Owners/moderators can hide or restore space-scoped post/resource associations without deleting underlying global content.
- Local visibility changes require reasons and retain actor/timestamp attribution.
- Append-only moderation actions record role changes, hides, and restores.
- Affected accounts can appeal eligible local hide decisions; review is attributable and cannot be self-resolved by the requester.
- Global Community Standards and Ripple-wide reporting remain separate and authoritative.
- Migration `20260831_0030_space_moderation.py` added the local moderation/audit state.
- Story 13.4 merged in PR #206.

## Story 13.5 — Community contribution context and privacy review

**Status:** In implementation.

### Current implementation slice

- Community contribution context is derived from existing **Helpful**, **Thoughtful**, and **Useful context** signals rather than stored as a mutable space reputation score.
- Evidence qualifies only when the recognized post is a currently visible post scoped to the space.
- Both the recognized author and recognizer must currently be explicit members of that same space.
- Self-recognition is ignored even if malformed/imported data contains it.
- Hidden space posts and globally removed posts do not contribute.
- If a recognizer or recognized author leaves the space, that evidence no longer appears in current community context.
- The space detail page exposes total signals, recognized posts, unique recognizers, and per-member component counts.
- Recognized members are displayed alphabetically rather than score-ranked.
- Context has no effect on feed ordering, global/topic reputation, moderation authority, verification, subscription status, or paid reach.
- `docs/COMMUNITY_CONTEXT_PRIVACY.md` documents anti-gaming, sensitive-trait, location, and future-expansion boundaries.
- No location collection is introduced. Future local coordination must use explicit coarse location and receive a separate privacy review; precise/background tracking remains out of scope.
- No schema migration is required.

### Acceptance criteria

- Only current member-to-member recognition on visible space posts contributes to space context.
- Signals from nonmembers, self-signals, hidden posts, and globally removed posts are excluded.
- Leaving the space removes that member's recognition evidence from current space context without deleting the underlying global signal record.
- The interface explains that the context is descriptive rather than a leaderboard/reputation score.
- Member context ordering is alphabetical and not based on signal totals, followers, engagement, payment, verification, or role.
- Tests cover evidence eligibility, membership changes, hidden/removed isolation, and user-facing explanation.
- Privacy documentation explicitly prohibits silent precise-location tracking and sensitive-trait inference.

### Story boundary

Story 13.5 does not create a cross-space reputation score, community leaderboard, recommendation input, moderator eligibility gate, location database, private spaces, or automated moderation signal. Any future use of community context for ranking, eligibility, or cross-community reputation requires a separately specified product/integrity decision.

## Definition of done

Sprint 13 is complete when Ripple has persistent communities with explicit membership, space-scoped conversations and resources, understandable moderation roles, community contribution context, and documented privacy/integrity boundaries while global Community Standards remain authoritative.
