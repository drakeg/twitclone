# Sprint 10 — Topic Reputation and Expertise

**Status:** In implementation.

## Goal

Help Ripple users find people who have demonstrated useful participation in specific topics without turning credibility into a global popularity score or a paid entitlement.

## Product hypothesis

Follower count and generic engagement are weak proxies for whether someone is consistently useful on a particular subject. Ripple already records constructive contribution signals and transparent fact-context review history. Topic-specific, explainable reputation can build on those foundations to help users discover useful contributors while avoiding a universal social score.

## Guardrails

- Reputation is topic-specific, never a single global human-worth or trust score.
- Paid status, subscriptions, identity badges, follower count, and raw impression volume do not increase topic reputation.
- Ripple does not infer political ideology, religion, health status, race, sexual orientation, or other sensitive traits to create topics, diversify reviewers, or score reputation.
- Users must be able to understand why a displayed reputation summary exists.
- Initial reputation is informational. It must not silently amplify or suppress feed reach.
- Self-awards and obvious reciprocal/gaming paths must not contribute.
- Reputation should be derived from auditable activity rather than a mutable administrator-entered score.
- Existing constructive signals and community-context review history remain meaningful on their own; Sprint 10 must not retroactively mislabel consensus as objective truth.

## Story 10.1 — Explicit topic foundation

**Status:** Completed.

**Goal:** Establish the topic vocabulary and association rules on which reputation can safely depend.

### Completed capabilities

- Adds normalized `Topic` records with duplicate-safe slugs.
- Adds `TweetTopic` associations without altering the mature `Tweet` table.
- Records whether an association came from an explicit composer topic or deterministic hashtag text.
- Lets authors add up to five comma-separated explicit topics in the post composer.
- Extracts deterministic hashtag topic candidates from public post text without using AI or sensitive-trait inference.
- Gives explicit composer choices precedence when the same normalized topic also appears as a hashtag.
- Existing posts require no backfill and simply have no topic associations until new topic-aware activity exists.
- Removed posts do not expose public topic associations.
- Timeline cards display associated topics for normal posts and reposts; Quote cards do not falsely inherit the original post's topics as if they belonged to the quoter.
- Migration `20260828_0023_topic_foundation.py` and focused regression coverage were merged in PR #182.

## Story 10.2 — Topic contribution evidence

**Status:** Completed.

**Goal:** Define which existing Ripple activities count as explainable topic contribution evidence.

### Completed capabilities

- Adds a derived `topic_contribution_evidence()` service rather than persisting a mutable reputation score.
- Only posts with an **explicit** topic association can create topic-contribution evidence. Hashtag-only associations remain discovery metadata and do not become expertise evidence by themselves.
- Helpful, Thoughtful, and Useful context signals on eligible posts are counted by signal type.
- Evidence also records the number of eligible posts, recognized posts, and unique recognizers.
- Self-signals are excluded even if an invalid historical/database row exists.
- Removed posts do not contribute.
- Deleting/toggling off a constructive signal immediately changes the derived evidence because the evidence is recomputed from source records.
- Followers, impressions, subscriptions, identity badges, and paid status are explicitly excluded from the evidence rules.
- No score, feed-ranking change, moderation weighting, paid boost, or global trust value is introduced.
- The evidence service and regression coverage were merged in PR #183.

### Explicit evidence rules

- Explicit post-topic association is required for constructive-signal evidence.
- Hashtag-only topic association does not establish expertise evidence.
- Removed/ineligible posts do not contribute.
- Self-recognition does not contribute.
- Multiple distinct constructive signals remain visible as separate dimensions rather than being silently collapsed into a weighted score.
- Unique recognizer counts are descriptive only; they are not an accuracy or expertise percentage.

## Story 10.3 — Explainable topic reputation summary

**Status:** In implementation.

**Goal:** Present useful topic history without collapsing it into a mysterious score.

### Current implementation slice

- Adds derived topic summaries for contributor/topic pairs; no reputation value is stored in the database.
- Uses plain-language levels with published thresholds across multiple visible dimensions:
  - Building contribution history — eligible explicit-topic posts exist but recognition thresholds are not yet met.
  - Emerging contributor — at least 1 constructive signal across at least 1 recognized post from at least 1 unique recognizer.
  - Recognized contributor — at least 3 constructive signals across at least 2 recognized posts from at least 2 unique recognizers.
  - Established contributor — at least 5 constructive signals across at least 3 recognized posts from at least 3 unique recognizers.
- Displays topic reputation on the user's profile alongside the underlying eligible-post, recognized-post, unique-recognizer, and per-signal counts.
- The profile explicitly states that topic reputation does not affect feed ranking or moderation authority.
- The summary explains that followers, impressions, paid plans, and verification do not affect it.
- Hashtag-only topics do not appear in topic reputation summaries.
- No schema migration is required because summaries are derived from Story 10.1/10.2 source records.

### Acceptance criteria

- Users can view an explainable summary for a contributor/topic pair.
- The summary shows underlying dimensions/counts and a plain-language level or status rather than only a magic number.
- New/low-data contributors are represented honestly rather than negatively.
- The UI explains what does and does not affect the summary.
- Reputation remains informational and does not alter feed ranking in this sprint.

## Story 10.4 — Discovery integration

**Goal:** Make topic expertise useful for discovery without turning it into a popularity leaderboard.

### Planned acceptance criteria

- Topic pages can surface contributors with demonstrated eligible contribution history.
- Discovery explains the ordering/qualification rule.
- Users are not ranked by a single cross-topic score.
- Paid products cannot purchase placement in topic reputation discovery.
- Empty/low-data topics degrade gracefully.

## Story 10.5 — Integrity and correction controls

**Goal:** Make the reputation system resilient enough to remain understandable and correctable.

### Planned acceptance criteria

- Deleted/removed/ineligible source activity stops contributing according to documented rules.
- Duplicate/self/gaming attempts are tested.
- Corrections to topic association are reflected in derived summaries without manual score editing.
- The documentation defines what happens when contribution signals are toggled off or source content is moderated.
- Any future use of reputation for elevated permissions requires a separate sprint/decision and is not implied by Sprint 10.

## Definition of done

Sprint 10 is complete when Ripple can associate eligible activity with explicit topics, derive explainable topic-specific contribution history, display it transparently, and use it for non-pay-to-win discovery without hidden reach ranking or sensitive-trait inference.

## Explicitly deferred

- Reputation-weighted moderation or community-context votes
- Reputation-based feed amplification/suppression
- Paid reputation boosts
- Cross-topic/global trust scores
- AI-inferred expertise or sensitive-interest profiles
- Communities/topic spaces, which are planned for Sprint 13
