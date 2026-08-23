# Product Vision

## Vision

Ripple will be a small, maintainable social networking platform that demonstrates sound Flask engineering while remaining understandable and inexpensive to operate. It should support a respectful community, practical creator tools, and modest optional revenue without making core participation paywalled.

## Product goals

1. Provide a reliable microblogging experience for accounts, posts, timelines, follows, interactions, messaging, media, polls, and scheduled content.
2. Preserve a simple local-development experience.
3. Apply secure defaults and keep secrets outside source control.
4. Maintain automated tests for critical behavior.
5. Keep architecture and operating procedures documented alongside the code.
6. Favor low-cost, incremental deployment choices over premature scale.
7. Support a safe, respectful community with reporting, moderation, and transparent resolution workflows.
8. Support sustainable optional monetization through clearly differentiated paid features while preserving a useful free account.
9. Give creators trustworthy analytics based on measurements Ripple actually collects rather than invented reach or engagement estimates.

## Target users

- People who want a smaller, respectful social community centered on conversation rather than hostility
- Creators and organizations that benefit from measured content-performance analytics
- Developers learning or demonstrating Flask application design
- Small private communities evaluating a self-hosted social application
- The repository owner as a portfolio, experimentation, and potential small-business project

## Current product model

Core social participation remains free. Ripple currently supports optional paid products with deliberately separate purposes:

- **Ripple+** — convenience and customization features such as extended scheduling, bookmark folders, profile themes/banners, and personal analytics.
- **Creator Pro** — measured creator/business analytics including impressions, profile visits, follower trends, per-post engagement, hashtag performance, and evidence-based performance insights.
- **Verified identity badge** — a paid identity add-on available only after Ripple approves the underlying identity. Payment never grants identity approval.

Paid-feature discovery should remain contextual and restrained. Ripple should not rely on intrusive pop-ups, deceptive urgency, or removal of basic social functionality to pressure users into subscribing.

## Non-goals for the current roadmap

- Competing at global social-network scale
- Building a mobile-native client before the web product and deployment model are stable
- Making core posting, following, messaging, or community participation require a paid subscription
- Selling identity approval or allowing payment to bypass verification review
- Introducing advertising solely to maximize impressions without a separate product decision and privacy/UX review
- Supporting federation before the core application is stable
- Introducing distributed infrastructure that creates avoidable cost or operational burden
- Presenting analytics metrics Ripple does not reliably measure

## Product principles

- Secure by default
- Respectful community by design
- Useful free participation remains intact
- Paid features provide additive value rather than artificial restrictions
- Analytics claims are grounded in measured data
- Small, reviewable changes
- Documentation is part of the product
- Tests accompany behavior changes
- Operational cost is considered before architecture is expanded
- Existing working behavior is preserved unless a sprint explicitly changes it
