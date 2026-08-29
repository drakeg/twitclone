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

**Status:** In implementation.

### Scope

- Add persistent public spaces with stable normalized slugs, names, descriptions, owners, and creation timestamps.
- Add explicit membership with one membership row per user/space.
- Establish only two roles initially: `owner` and `member`.
- The creator becomes the owner and an owner membership is created atomically with the space.
- Any signed-in user can explicitly join a public space and later leave it.
- Owners cannot leave until a future ownership-transfer workflow exists.
- Provide `/spaces/` discovery, `/spaces/create`, and stable `/spaces/<slug>` detail pages.
- Public visitors can discover and read space identity/description/member-count information without joining.
- No feed ranking, global reputation, paid entitlement, verification, or inferred-interest effect is attached to membership.

### Acceptance criteria

- Space slugs are unique and normalized into stable URLs.
- Creation requires authentication and valid name/description input.
- Creation records both the durable space owner and the matching owner membership.
- Duplicate memberships are prevented by the database.
- Join/leave operations are authenticated and idempotent from the user's perspective.
- An owner cannot remove their own final ownership membership through the ordinary leave action.
- Public space discovery works without authentication.
- Regression coverage proves creation, uniqueness, join/leave, owner boundary, and public discovery.
- Migration `20260829_0027_space_foundation.py` upgrades from the current `0026` head.

### Story boundary

Story 13.1 does **not** add space-specific posts, resources, private communities, invitations, moderator roles, bans, local/precise location, or ownership transfer. Those capabilities require separate acceptance criteria so membership and authority semantics remain reviewable.

## Story 13.2 — Space-specific conversations

**Status:** Planned.

Allow posts to be explicitly published into a joined space while preserving a clear distinction between global timeline content and community-scoped conversation context.

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
