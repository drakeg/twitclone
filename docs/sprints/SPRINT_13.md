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

**Status:** Completed.

- `SpacePost` links an existing durable `Tweet` to exactly one space.
- Only explicit members can publish into a space; public visitors can read current public-space conversations.
- Space conversations are deterministic newest-first and clearly labeled as space-scoped.
- Space-scoped posts, plus reposts/quotes referencing them, are excluded from global All Ripple, Following, Quiet, and Topic feeds.
- Space posting does not change global reputation, verification, entitlement, or feed ranking.
- Story 13.2 merged in PR #202.

## Story 13.3 — Space resources and knowledge

**Status:** In implementation.

### Current implementation slice

- Add an attributable `SpaceResource` association connecting an existing Sprint 11 durable resource to a public space.
- Migration `20260829_0029_space_resources.py` advances from the `0028` space-post head.
- Associations are many-to-many across spaces and resources, with one link per space/resource pair.
- Every link records the member who explicitly added the resource and the link timestamp.
- Linking never copies or changes resource ownership, revision history, topics, lifecycle state, or global discovery placement.
- Any explicit space member can link a currently visible resource into the space knowledge list.
- Public readers can browse linked resources because current Sprint 13 spaces are public.
- Removed resources are excluded from space knowledge and cannot be newly linked.
- Space knowledge is ordered by link recency with a deterministic ID tie-breaker; this is a browsing order, not a quality score.
- The member who created a link can undo that association without deleting or modifying the resource itself.
- Other members, including the owner, do not receive link-removal authority in this story; broader local moderation powers are intentionally deferred to Story 13.4.

### Acceptance criteria

- A member can link an existing visible resource and the UI attributes the link to that member.
- A nonmember cannot link resources into the space.
- Public readers can see linked visible resources and follow them to the durable resource detail/history.
- Linking preserves the original resource owner and immutable revision history.
- Removed resources are hidden from space knowledge and cannot be newly linked.
- Duplicate space/resource associations are prevented by the database constraint.
- The original linker can remove only the space association; the resource and revisions remain intact.
- Another member cannot remove someone else's association before Story 13.4 defines local moderation authority.
- Membership, link count, paid status, verification, follower count, and engagement do not influence global resource placement or reputation.
- Tests cover attribution, membership enforcement, removal visibility, provenance preservation, unlink behavior, and authorization boundaries.

### Story boundary

Story 13.3 is space-local curation, not resource ownership transfer or a second knowledge store. It does not add space-only resource copies, space-specific revision forks, quality scoring, moderator curation powers, private resources, or paid placement. Those would require separate product and integrity decisions.

## Story 13.4 — Roles and moderation boundaries

**Status:** Planned.

Define understandable moderator/owner powers, audit history, removal/appeal behavior, and the relationship between local moderation and global Community Standards.

## Story 13.5 — Community contribution context and privacy review

**Status:** Planned.

Add community-specific contribution context where justified and document privacy/anti-gaming rules. Any location-oriented coordination must use explicit coarse location and must not silently track precise location.

## Definition of done

Sprint 13 is complete when Ripple has persistent communities with explicit membership, space-scoped conversations and resources, understandable moderation roles, community contribution context, and documented privacy/integrity boundaries while global Community Standards remain authoritative.
