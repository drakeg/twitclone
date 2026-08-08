# ADR-0017: Normalized timeline data contract

- Status: Accepted
- Date: 2026-08-07
- Sprint: 3
- Story: 3.2

## Context

The timeline combined tweets, retweets, and polls through a SQL union with fields
that did not share the same meaning. Retweet rows placed a Tweet ID in the
`content` field and used the Retweet ID for actions that require a Tweet ID.
Quotes were not included at all. The template therefore could not consistently
render content provenance or generate valid actions.

## Decision

Introduce a timeline service that normalizes tweets, retweets, quotes, and polls
into one explicit view contract.

Every item provides its source identity, display content, timestamp, type, actor,
media, optional original-tweet context, optional poll state, and the Tweet ID to
use for retweet, quote, and bookmark actions.

- Tweets display their own content, author, and media.
- Retweets display the original Tweet content and media while identifying both
  the retweeter and original author.
- Quotes display the quote commentary plus the original Tweet and author.
- Polls preserve their existing question, options, activity, and viewer-vote
  behavior.

Sort the assembled items by their activity timestamp, newest first. Preserve the
existing scheduled-Tweet filter; broader scheduled-content visibility is a
separate story.

## Consequences

### Positive

- Every rendered field has one documented meaning.
- Quotes now participate in the main timeline.
- Retweets render content rather than numeric IDs.
- Timeline actions always receive a Tweet ID.
- Rendering and data behavior can evolve behind one service boundary.

### Negative

- Timeline assembly currently performs separate queries per content type.
- Quotes and retweets still act on the original Tweet because the current models
  do not support interacting with those records as standalone posts.
- Pagination requires a later query strategy rather than slicing this in-memory
  result.

## Guardrails

- Scheduled visibility, pagination, ownership, and duplicate-interaction rules
  remain separate stories.
- Changes to the normalized item keys require service and template tests in the
  same pull request.
