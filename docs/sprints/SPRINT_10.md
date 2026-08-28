# Sprint 10 — Topic Reputation and Expertise

**Status:** Completed.

## Goal

Help Ripple users find people who have demonstrated useful participation in specific topics without turning credibility into a global popularity score or paid entitlement.

## Guardrails

- Reputation is topic-specific, never a global trust or human-worth score.
- Paid status, subscriptions, identity badges, follower count, and raw impression volume do not increase topic reputation.
- Sensitive personal traits are not inferred to create topics or score reputation.
- Users can understand why a displayed reputation summary exists.
- Reputation is informational and does not silently alter feed reach or moderation authority.
- Self-awards and obvious gaming paths do not contribute.
- Reputation is derived from auditable activity rather than a mutable administrator-entered score.

## Story 10.1 — Explicit topic foundation

**Status:** Completed.

Normalized, duplicate-safe topics and post-topic associations distinguish explicit author choices from deterministic hashtags. Authors can select up to five explicit topics. Hashtags remain discovery metadata rather than automatic expertise evidence. Migration `20260828_0023_topic_foundation.py` and regression coverage merged in PR #182.

## Story 10.2 — Topic contribution evidence

**Status:** Completed.

`topic_contribution_evidence()` derives evidence instead of storing a score. Only explicit topic associations qualify. Helpful, Thoughtful, and Useful context signals remain separate dimensions alongside eligible posts, recognized posts, and unique recognizers. Self-signals, removed posts, followers, impressions, paid status, and verification are excluded. Merged in PR #183.

## Story 10.3 — Explainable topic reputation summary

**Status:** Completed.

Contributor/topic summaries are derived and displayed on profiles with published plain-language levels and the underlying evidence dimensions. Hashtag-only topics do not appear. Profiles state that topic reputation does not affect feed ranking or moderation authority. Merged in PR #184.

## Story 10.4 — Discovery integration

**Status:** Completed.

`/topic/<slug>` surfaces contributors with eligible explicit-topic history. Qualification and ordering are disclosed and do not use paid status, followers, impressions, subscriptions, or verification. Existing low-data topics degrade gracefully and unknown slugs return 404. Merged in PR #186.

## Story 10.5 — Integrity and correction controls

**Status:** Completed.

Authors can correct explicit topics on their own non-removed posts. Hashtag associations are rebuilt deterministically from unchanged text. Moving or clearing an explicit topic immediately changes derived evidence without editing a reputation record. Non-authors cannot change another author's topics. Toggled-off constructive signals stop contributing, multiple signal categories from one person still count as one unique recognizer, and removed/moderated posts stop contributing to summaries and discovery. Merged in PR #187.

## Integrity behavior reference

- **Constructive signal toggled off:** the source row is deleted and no longer counts.
- **Post removed/moderated:** the post no longer qualifies as evidence or contributor-discovery input.
- **Explicit topic corrected:** evidence follows the current explicit association; no reputation record is manually moved.
- **Explicit topic cleared but hashtag remains:** the topic remains discoverable from text but contributes zero expertise evidence from that post.
- **Multiple signal categories from one recognizer:** categories remain separate while unique-recognizer count remains one.
- **Paid/follower changes:** no reputation evidence or discovery placement changes.

## Sprint outcome

Sprint 10 delivered explicit topics, reproducible topic contribution evidence, explainable profile summaries, transparent contributor discovery, and source-level correction controls without global trust scoring, pay-to-win placement, hidden feed effects, or manual reputation editing.

## Explicitly deferred

- Reputation-weighted moderation or community-context votes
- Reputation-based feed amplification or suppression
- Paid reputation boosts
- Cross-topic/global trust scores
- AI-inferred expertise or sensitive-interest profiles
- Elevated permissions based on topic reputation
- Communities/topic spaces, planned for Sprint 13
