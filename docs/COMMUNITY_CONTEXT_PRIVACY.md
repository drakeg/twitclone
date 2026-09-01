# Community Contribution Context — Privacy and Integrity

Sprint 13 community contribution context is deliberately narrower than a reputation or recommendation system.

## What Ripple uses

Ripple derives community context only from data already created through explicit actions:

- a post explicitly published into a community space;
- a current explicit membership in that same space; and
- an existing constructive signal: **Helpful**, **Thoughtful**, or **Useful context**.

For a signal to appear in community context, both the recognized author and the recognizer must currently be members of the space, the post must still be visible in that space, and the recognizer must be someone other than the author.

The displayed member list is alphabetical. Counts are descriptive evidence, not a combined score.

## What Ripple does not use

Community context does not use or infer:

- browsing history;
- precise or background location;
- political ideology, religion, health status, race, sexuality, or other sensitive traits;
- follower counts;
- impression or engagement velocity;
- verification status;
- paid plan or entitlement status;
- global topic reputation; or
- moderator/owner role as a quality signal.

Community context does not alter global or space feed ordering, global reputation, moderation authority, verification, subscriptions, or paid reach.

## Anti-gaming boundaries

- Self-recognition is ignored even if malformed/imported data contains it.
- Signals from nonmembers do not count toward space context.
- Signals on hidden space posts or globally removed posts do not count.
- If a recognizer or author leaves the space, that evidence stops appearing in the current space context.
- Multiple distinct signal types may describe the same post, but the interface exposes the component counts instead of collapsing them into a hidden score.
- No threshold grants moderator powers, promotion, feed placement, or other privileges.

These rules make manipulation less valuable: increasing a displayed count cannot purchase reach or authority.

## Location and local coordination boundary

Sprint 13 does **not** add location collection or location-based membership. If Ripple later adds local-community coordination, it must be a separately specified feature with all of the following safeguards:

- location is supplied explicitly by the user;
- the default representation is coarse (for example, city/region), not precise coordinates;
- no background or silent location tracking;
- no inference of home/work address or routine travel patterns;
- a clear way to remove or change the disclosed location; and
- a privacy review before location influences discovery or visibility.

Precise latitude/longitude, continuous device location, and hidden location-derived profiling are outside the authorized Sprint 13 scope.

## Future changes

Any proposal to turn community context into a score, ranking input, eligibility gate, automated moderation signal, or cross-community reputation measure requires a new product specification, explicit user-facing explanation, privacy/integrity review, and regression coverage. It must not be introduced as an incidental extension of these descriptive counts.
