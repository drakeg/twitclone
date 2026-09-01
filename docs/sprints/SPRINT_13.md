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
- Explicit membership records establish `owner` and `member` roles with one membership per user/space.
- Creators become owners atomically; signed-in users can explicitly join and leave public spaces.
- Owners cannot leave through the ordinary leave flow until ownership transfer exists.
- `/spaces/`, `/spaces/create`, and `/spaces/<slug>` provide public discovery and stable space identity.
- Membership has no effect on feed ranking, global reputation, paid entitlement, or verification.
- Story 13.1 merged in PR #201.

## Story 13.2 — Space-specific conversations

**Status:** Completed.

- `SpacePost` links an existing durable `Tweet` to exactly one space.
- Only explicit members can publish into a space; public visitors can read current public-space conversations.
- Space conversations are deterministic newest-first and clearly labeled as space-scoped.
- Space-scoped posts, plus reposts/quotes referencing them, are excluded from global All Ripple, Following, Quiet, and Topic feeds.
- Space posting does not change global reputation, verification, entitlement, or feed ranking.
- Story 13.2 merged in PR #202.

## Story 13.3 — Space resources and knowledge

**Status:** Completed.

- `SpaceResource` associates an existing Sprint 11 durable resource with a public space without copying it.
- Every association records the member who explicitly linked it and when.
- Any explicit member can link a currently visible resource; the original linker can remove only that association.
- Public readers can follow linked resources back to the original durable resource and revision history.
- Removed resources are excluded from space knowledge and cannot be newly linked.
- Link recency is browsing order only; membership, link counts, payment, verification, followers, and engagement do not change global placement or reputation.
- Story 13.3 merged in PR #205.

## Story 13.4 — Roles and moderation boundaries

**Status:** In implementation.

### Current implementation slice

- Expand explicit space roles to `owner`, `moderator`, and `member`.
- Only owners can promote a member to moderator or demote a moderator back to member.
- Moderator authority is strictly space-local: moderators and owners can hide or restore a `SpacePost` or `SpaceResource` association without deleting the underlying global Tweet or durable Resource.
- Local visibility state records who hid an item, when, and the required reason.
- Append-only `SpaceModerationAction` records preserve role changes, local hides, and local restores with actor, target, affected account, reason, and timestamp.
- `SpaceModerationAppeal` gives the affected post author or resource linker one attributable appeal for a hide decision.
- Appeals are reviewed by an owner/moderator other than the requester. Approval restores only the space-local association and creates a separate restore audit action; denial retains the local hide.
- The space UI explains role powers, local-vs-global moderation, moderation history, and appeal status.
- Global Community Standards and Ripple-wide reporting remain separate and authoritative; a local moderator cannot use space powers to erase global content or alter global moderation state.
- Migration `20260831_0030_space_moderation.py` advances from the `0029` space-resource head and uses SQLite-compatible batch alterations for existing space tables.

### Acceptance criteria

- Owners can grant/revoke moderator role; moderators cannot grant roles or modify ownership.
- Ordinary members cannot use moderation routes.
- Owners/moderators can hide a space-scoped post with a required reason and public space readers stop seeing it.
- Hiding a space post does not set the underlying Tweet's global `is_removed` flag.
- Owners/moderators can hide a resource association without removing or altering the durable Resource or its revision history.
- Every local hide/restore and moderator role change creates an attributable audit record.
- The affected account can appeal an eligible local hide and cannot appeal another account's moderation action.
- Appeal approval restores local visibility without changing global content state; appeal resolution is attributable.
- Paid status, verification, followers, engagement, and global reputation do not grant local moderation authority.
- Tests cover role authorization, local/global isolation, audit attribution, resource preservation, appeal submission, and appeal restoration.

### Story boundary

Story 13.4 is intentionally local moderation, not a replacement for Ripple-wide Community Standards enforcement. It does not add private spaces, bans/suspensions, ownership transfer, moderator deletion of global posts/resources, automated moderation scores, paid moderation privileges, or hidden trust/ranking effects. Those require separately specified product and integrity decisions.

## Story 13.5 — Community contribution context and privacy review

**Status:** Planned.

Add community-specific contribution context where justified and document privacy/anti-gaming rules. Any location-oriented coordination must use explicit coarse location and must not silently track precise location.

## Definition of done

Sprint 13 is complete when Ripple has persistent communities with explicit membership, space-scoped conversations and resources, understandable moderation roles, community contribution context, and documented privacy/integrity boundaries while global Community Standards remain authoritative.
