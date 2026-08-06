# ADR-0011: Timeline Blueprint

- Status: Accepted
- Date: 2026-08-05
- Sprint: 2
- Story: 2.6

## Context

After authentication extraction, the primary timeline and post workflow remains
in `app.py`. It is the next cohesive route group and exercises the package-owned
extensions, models, and utilities established by earlier Sprint 2 stories.

The existing templates refer to unqualified endpoint names. The tweet route also
contains a legacy `/dm` command path that overlaps with messaging ownership.
Changing either behavior would expand this structural story into product work.

## Decision

Create `twitclone.timeline` with an `timeline` Blueprint owning:

- `/`
- `/tweet`
- `/uploads/<filename>`
- `/retweet/<tweet_id>`
- `/quote/<tweet_id>`

Register these routes from the application factory with their existing endpoint
names. Preserve templates, redirects, authorization, upload behavior, scheduling,
timeline query composition, flash messages, and the `/dm` compatibility path.

Bookmarking, profiles, messaging pages, polls, notifications, and search remain
outside this Blueprint. The old functions in `app.py` are temporarily dormant
compatibility code and no longer own URL rules in the supported factory path.

## Consequences

### Positive

- The main read/write post workflow has package ownership.
- Existing URLs and template endpoint references remain stable.
- Timeline code imports shared package models, extensions, and utilities directly.
- Later Blueprint stories can remain narrowly scoped.

### Negative

- Unqualified endpoint compatibility again requires a Blueprint registration hook.
- Dormant timeline implementations remain temporarily in `app.py` until final
  monolith cleanup.
- The legacy `/dm` command keeps a messaging dependency inside the tweet route.

## Guardrails

- Timeline behavior changes require a separate story.
- No templates, models, migrations, dependencies, or UI change in this story.
- The `/dm` path moves only during a separately reviewed behavior or messaging
  change.
