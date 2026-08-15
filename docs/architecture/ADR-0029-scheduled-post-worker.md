# ADR-0029: Dedicated scheduled-post worker

- Status: Accepted
- Date: 2026-08-15
- Sprint: 5
- Story: 5.5

## Context

The web module started an in-process scheduler at import time. Multi-worker and
reload environments could create duplicate schedulers, while its query required
scheduled Tweets to have a null timestamp even though Tweet creation supplies a
timestamp. The job therefore could not process normal scheduled rows.

## Decision

- Web startup never starts scheduled processing.
- A dedicated worker polls an idempotent package operation.
- Due Tweets are selected by non-null `scheduled_at <= now`, published using the
  scheduled instant as their timestamp, and cleared of `scheduled_at` in one
  transaction.
- Compose runs migration, web, and worker as distinct services sharing one
  database/media volume; web and worker wait for migration completion.
- A stopped scheduler object and wrapper remain temporarily for import
  compatibility.

## Consequences

- Web replicas cannot accidentally multiply scheduler jobs.
- Worker restarts and repeated processing are safe.
- Compose mirrors the intended process separation for local testing.
- Production deployment must run exactly one worker until database-level job
  claiming is introduced for horizontal worker scaling.

## Guardrails

- Scheduled work must not start during application import.
- Processing must remain idempotent and covered at the exact due boundary.
