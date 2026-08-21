# Backup, restore, media, and rollback runbook

This runbook defines Ripple's durable-state boundaries and the minimum recovery
procedure for a public deployment. It complements the database migration
procedure in [`database.md`](database.md) and the process contract in
[`production-serving.md`](production-serving.md).

## Durable state inventory

| State | Production system of record | Backup requirement |
| --- | --- | --- |
| Accounts, posts, relationships, billing state, and metadata | Managed PostgreSQL 18 | Provider point-in-time recovery plus an independent encrypted logical backup |
| Uploaded original images and thumbnails | Private S3-compatible object storage | Versioning plus an independent bucket copy |
| Application image and source | Immutable image tagged with the Git SHA | Retain at least the current and previous known-good image |
| Secrets | Hosting-platform secret manager | Documented recreation and rotation procedure; never include secret values in backups |
| Logs and metrics | External platform collection | Retention appropriate to incident investigation; logs are not application backups |

Container filesystems are disposable. Production must not use `static/uploads`
inside an ephemeral container as its media system of record. Ripple provides
filesystem and private S3-compatible adapters. Production startup requires S3;
local development retains the filesystem path. Existing media must be copied to
the configured bucket before cutover.

Local Docker Compose is intentionally different: `/data/twitclone.db` and
`/data/uploads` share the `twitclone_data` named volume. This preserves local
developer data across `docker compose down`. Running `docker compose down -v`
erases both and must never appear in a backup or recovery procedure.

## Recovery objectives

The initial low-traffic service targets:

- recovery point objective (RPO): no more than 24 hours for independent backups;
  use the database provider's point-in-time recovery for a smaller database RPO;
- recovery time objective (RTO): four hours during the operator's supported
  response window;
- backup retention: seven daily, four weekly, and three monthly independent
  database and media copies;
- one successful restore rehearsal before launch and at least quarterly after launch.

These are operating targets, not guarantees. Record actual backup and restore
durations and revise the targets when data volume grows.

## Backup procedure

Perform database and media backups as one recorded recovery set. They cannot be
perfectly atomic, so record start/end times and reconcile media created during
that interval after a restore.

1. Record the release SHA, Alembic revision, UTC start time, database cluster,
   media bucket, and operator in the recovery log.
2. Confirm the managed database's latest automatic backup is healthy.
3. Create an encrypted custom-format logical backup from a trusted one-shot job:

   ```bash
   pg_dump --format=custom --no-owner --no-acl --file=ripple.dump "$DATABASE_URL"
   pg_restore --list ripple.dump
   ```

4. Upload `ripple.dump` to an encrypted backup destination separate from the
   live database. Do not place credentials in its filename, command output, or metadata.
5. Confirm object versioning is enabled on the live media bucket. Copy media to
   an independent backup bucket or account without `--delete` semantics.
6. Compare source and backup object counts and total bytes. Investigate any mismatch.
7. Record backup identifiers, checksums, sizes, UTC completion time, and retention expiry.
8. Apply retention only after the new recovery set has been verified.

Versioning protects against ordinary overwrites and deletions but is not an
independent backup. Account compromise or bucket deletion can affect every
version in the live account.

## Restore rehearsal and recovery

Never test a restore over the production database or live media bucket.

1. Select a recovery set and verify its recorded checksum.
2. Restore the managed PostgreSQL backup to a **new** cluster, or create an empty
   isolated database and restore the logical dump:

   ```bash
   pg_restore --clean --if-exists --no-owner --no-acl --dbname="$RESTORE_DATABASE_URL" ripple.dump
   ```

3. Restore media to a new private bucket. Keep public listing disabled.
4. Start the matching application image in an isolated environment using only
   the restored database and bucket.
5. Run `flask --app application db current`; it must match the recorded revision
   before any upgrade is attempted.
6. Verify readiness, login, timeline reads, image retrieval, row counts, and a
   representative sample of relationships and billing entitlements.
7. Record elapsed time, missing data, reconciliation work, and whether the RPO
   and RTO were met.
8. Destroy rehearsal resources only after the result and evidence are recorded.

For a real incident, keep web and worker processes stopped until validation is
complete. Cut over secrets or connection settings to the new database and media
bucket, start one web process, verify health and core reads, then start exactly
one worker. Preserve the damaged resources for investigation when safe to do so.

## Release rollback decision

| Situation | Response |
| --- | --- |
| Application regression; schema remains backward compatible | Roll the web and worker image back to the previous known-good SHA. Do not downgrade the database. |
| Additive migration plus application regression | Prefer the previous image if compatible; otherwise deploy a forward fix. |
| Destructive or incompatible migration, but data is intact | Keep writers stopped and use the release-specific rehearsed forward or restore plan. |
| Data corruption or accidental deletion | Restore to new database/media resources from the selected recovery set and reconcile later writes. |
| Secret compromise | Stop affected access, rotate the secret, invalidate sessions or provider credentials as appropriate, then redeploy. |

After every rollback, verify `/health/live`, `/health/ready`, login, a timeline
read, media retrieval, and scheduled-worker logs. Record the failed and restored
SHAs, database revision, recovery-set identifiers, timestamps, operator, impact,
and follow-up issue.

## Launch gate

Public traffic is not approved until all of these are true:

- the production media adapter uses private durable object storage and existing
  media has been copied and verified;
- database point-in-time recovery and independent logical backups are enabled;
- media versioning and an independent media copy are enabled;
- a full restore rehearsal meets the documented RPO and RTO;
- the prior image and migration compatibility decision are recorded per release;
- backup failure alerts have an owner and tested notification path.
