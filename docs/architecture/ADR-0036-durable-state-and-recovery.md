# ADR-0036: Durable state and recovery boundaries

- Status: Accepted
- Date: 2026-08-20
- Sprint: 6
- Story: 6.4

## Context

Ripple has explicit production web, worker, migration, and PostgreSQL
boundaries, but uploaded media still uses a local filesystem and there was no
complete backup, restore, rollback, or cost contract. Container-local storage
would make uploads disappear during replacement or scaling.

## Decision

- Managed PostgreSQL remains the production system of record for relational data.
- Private S3-compatible object storage will own original images and thumbnails.
- Container filesystems are disposable and never authoritative.
- Database backups combine provider recovery with independent logical dumps.
- Media recovery combines object versioning with an independent bucket copy.
- Restores always target new isolated resources before cutover.
- Production database downgrades remain manual and exceptional; application
  rollback is preferred only when schema compatibility is established.
- Public launch is blocked until the object-storage adapter and a complete
  restore rehearsal satisfy the runbook.

## Consequences

- Local Compose remains simple and retains SQLite and uploads in its named volume.
- Production gains explicit recovery objectives and evidence requirements.
- Object storage adds a dependency and operating cost but removes reliance on
  ephemeral or instance-local media.
- A later implementation increment must add the storage adapter without changing
  existing image URLs or upload behavior.
