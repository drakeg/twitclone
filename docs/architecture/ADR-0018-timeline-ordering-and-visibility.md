# ADR-0018: Timeline ordering and scheduled visibility

- Status: Accepted
- Date: 2026-08-08
- Sprint: 3
- Story: 3.3

## Context

The normalized timeline filters future scheduled Tweets, but retweets and quotes
of those Tweets were still visible. Once a scheduled Tweet became visible, it
used its original database timestamp and could appear at the time it was created
rather than the time it was scheduled to publish.

Sorting only by timestamp also left exact ties dependent on database query order.

## Decision

Define the following timeline rules against the request's injected `now` value:

- Unscheduled Tweets are visible immediately.
- Scheduled Tweets are hidden while `scheduled_at > now` and visible when
  `scheduled_at <= now`.
- Retweets and quotes are hidden whenever their original Tweet is hidden.
- Visible scheduled Tweets use `scheduled_at` as their timeline timestamp.
- Items sort by timeline/activity timestamp descending.
- Exact timestamp ties sort by Tweet, Retweet, Quote, then Poll.
- Same-type ties sort by higher source ID first.

Apply visibility in database queries before normalizing retweets and quotes.

## Consequences

### Positive

- Scheduled content cannot leak through retweets or quotes.
- Scheduled Tweets appear at their intended publication position.
- Timeline ordering is deterministic and testable.
- The fixed-clock service remains ready for pagination work.

### Negative

- Type precedence is an explicit product convention for otherwise indistinguishable
  activity times.
- Existing scheduled rows retain their original database timestamp even though
  timeline presentation uses `scheduled_at`.
- The background scheduler remains transitional and is not redesigned here.

## Guardrails

- Pagination must preserve this exact ordering tuple.
- Scheduler execution, timezone migration, and scheduled-post editing require
  separate stories.
- New timeline content types must receive an explicit tie priority and visibility
  rule.
