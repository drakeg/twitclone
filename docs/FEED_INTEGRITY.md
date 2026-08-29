# Ripple Feed Integrity and Measurement

Ripple's feed system is intentionally transparent and deterministic. This document defines the product and engineering boundaries established by Sprint 12.

## Ordering contract

All feed modes are **newest-first**. There is no hidden relevance score layered on top of chronology.

Supported modes:

- **All Ripple** — all currently visible content.
- **Following** — content acted/published by accounts the viewer explicitly follows, plus the viewer's own activity.
- **Topic** — content carrying an author-selected explicit topic association; hashtag-only associations do not qualify.
- **Quiet** — the viewer plus reciprocal-follow relationships, with repost amplification removed.

## Allowed inclusion inputs

A feed may use only transparent data needed to implement the selected mode: content visibility, the account that authored or performed an action, explicit/reciprocal follow relationships, author-selected explicit topics, content type, and timestamp.

## Inputs that must not rank organic feed content

The following must not influence organic ordering or purchase placement:

- likes or constructive-contribution totals;
- repost, reply, or quote totals;
- impression or profile-visit totals;
- follower count;
- verification status;
- paid subscription or entitlement;
- engagement velocity;
- inferred emotional state;
- inferred political ideology;
- inferred sensitive interests.

If Ripple ever introduces a non-chronological recommendation mode, that must be a separately specified feature with an explicit user-facing explanation and new review of privacy, accessibility, integrity, and anti-gaming boundaries.

## Measurement policy

Sprint 12 does not add feed-choice or topic-query history collection.

Ripple may continue using the analytics data it already records for aggregate/creator reporting after feed selection, including deduplicated post impressions, profile visits, and follower snapshots. Those reporting signals do not feed back into timeline inclusion or ordering.

This separation is intentional: measuring whether content was seen is not permission to optimize the feed for engagement.

## Anti-gaming expectations

Because organic feeds are chronological or explicitly filtered, manipulating engagement totals cannot improve placement. Topic discovery requires an explicit author-selected topic rather than inferred interest or raw hashtag velocity. Quiet mode is based on reciprocal relationships and removes repost amplification.

Abuse controls, moderation state, and content removal may still affect whether content is eligible to be shown at all. They do not create a paid or popularity ranking tier.

## Privacy boundaries

Ripple does not need to infer sensitive traits to implement Sprint 12 feed modes. Feed mode selection and topic query history are not retained as new analytics events in this sprint. Existing analytics remain scoped to creator/aggregate reporting and are not ranking inputs.

## Regression expectations

Automated coverage must preserve:

- deterministic newest-first ordering;
- explicit relationship boundaries for Following and Quiet;
- explicit-topic semantics for Topic mode;
- exclusion of repost amplification from Quiet;
- rejection of non-persistent modes as stored defaults;
- separation between analytics/reporting data and feed ordering.
