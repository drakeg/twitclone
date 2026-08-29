# Sprint 13 — Communities and Topic Spaces

**Status:** In implementation.

## Goal

Create persistent spaces where conversations, resources, and topic contribution history can coexist without weakening Ripple's global Community Standards or turning community membership into a ranking signal.

## Product principles

- Membership is explicit; Ripple does not infer community membership from browsing, location, ideology, or other sensitive traits.
- Community membership, ownership, or future moderation roles do not purchase or imply global reach, reputation, verification, or paid status.
- Global Community Standards remain authoritative inside every space.
- Roles and moderation powers must be understandable and auditable before additional privileges are introduced.
- Story 13.1 spaces are public. Private/local coordination requires separately defined privacy and location boundaries.

## Story 13.1 — Persistent space and membership foundation

**Status:** Completed.

- Persistent public spaces have stable normalized slugs, names, descriptions, owners, and creation timestamps.
- Explicit membership records establish `owner` and `member` roles with one membership per user/space.
- Creators become owners atomically; signed-in users can explicitly join and leave public spaces.
- Owners cannot leave through the ordinary leave flow until ownership transfer exists.
- `/spaces/`, `/spaces/create`, and `/spaces/<slug>` provide public discovery and stable space identity.
- Membership has no effect on feed ranking, global reputation, paid entitlement, or verification.
- Story 13.1 merged in PR #201.

## Story 13.2 — Space-specific conversations

**Status:** In implementation.

### Current implementation slice

- Add a one-to-one `SpacePost` scope record linking an existing durable `Tweet` to exactly one space.
- Migration `20260829_0028_space_posts.py` advances from the `0027` space-foundation head.
- Only explicit members, including the owner, may publish a space-scoped post.
- Public visitors may read conversations because Story 13 spaces are public.
- Space conversations render newest-first and are clearly labeled as space-scoped.
- Space-scoped posts are excluded from All Ripple, Following, Quiet, and Topic global feeds.
- Reposts and quotes whose source is a space-scoped post are also excluded from global feed assembly, preventing indirect amplification from silently changing the original scope.
- Posting in a space does not change global reputation, verification, entitlement, or feed ranking.
- The first slice intentionally keeps the space composer text-only; media, polls, scheduling, conversation intent, and independent topic metadata require separately reviewed space semantics rather than silently inheriting global behavior.

### Acceptance criteria

- A member can publish a valid space post and see it on the space page.
- A nonmember cannot publish into the space.
- Public readers can view visible space conversations without joining.
- Removed posts are not rendered in the space conversation list.
- Space conversations are deterministically newest-first.
- A space-scoped post never appears in the global All Ripple, Following, Quiet, or Topic feed.
- Repost/quote records referencing a space-scoped source do not cause the content to appear globally.
- The UI states that space posts remain in the space and that global Community Standards still apply.
- Regression coverage proves membership enforcement, public reading, ordering, and global-feed isolation.

### Story boundary

Story 13.2 does not create private spaces, space-only visibility ACLs, moderator powers, space resources, cross-posting, or a second engagement/ranking system. Space-local removal and appeals are defined in Story 13.4 together with role authority and audit requirements.

## Story 13.3 — Space resources and knowledge

**Status:** Planned.

Connect Sprint 11 durable resources to spaces with explicit attribution and discovery boundaries.

## Story 13.4 — Roles and moderation boundaries

**Status:** Planned.

Define understandable moderator/owner powers, audit history, removal/appeal behavior, and the relationship between local moderation and global Community Standards.

## Story 13.5 — Community contribution context and privacy review

**Status:** Planned.

Add community-specific contribution context where justified and document privacy/anti-gaming rules. Any location-oriented coordination must use explicit coarse location and must not silently track precise location.

## Definition of done

Sprint 13 is complete when Ripple has persistent communities with explicit membership, space-scoped conversations and resources, understandable moderation roles, community contribution context, and documented privacy/integrity boundaries while global Community Standards remain authoritative.
