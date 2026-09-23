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

### Migrating existing filesystem media

Configure the application for the destination S3 bucket using the variables in
[`configuration.md`](configuration.md), while keeping the existing upload
directory available to the one-shot migration process. First preview the copy:

```bash
flask --app application migrate-media-to-s3 --source /path/to/uploads --dry-run
```

Then perform and verify the copy:

```bash
flask --app application migrate-media-to-s3 --source /path/to/uploads
```

The command compares every regular, non-hidden top-level source file with its
destination object by SHA-256 content digest. It verifies each newly written
object by reading it back. A repeat run is safe and should report all objects as
unchanged. Differing destination objects are reported as conflicts and produce
a failed command; review them before using `--overwrite`. Do not remove the
source directory or cut traffic over until the final run has no conflicts and
the application can retrieve a representative sample of migrated images.

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

Record the exercise using
[`templates/restore-rehearsal-record.md`](templates/restore-rehearsal-record.md).
Store the completed record in the approved operational system, not this public
repository, and link it from the release readiness record.

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

## Deployment preflight

After applying migrations and before enabling public traffic, run this one-shot
command in the production environment with the same configuration and network
access as the web process:

```bash
flask --app application deployment-preflight
```

The command fails unless `TWITCLONE_ENV=production`. It verifies database
connectivity, confirms the database is at every repository migration head, and
writes, reads, and deletes a uniquely named private media probe. A successful
result ends with `Deployment preflight passed.` and leaves no probe object.

Treat any failure as a blocked release. The command does not replace a backup,
restore rehearsal, application smoke test, or monitoring check. After it passes,
start one web process, verify both health endpoints and core reads, then start
exactly one scheduled worker. Record the command result with the release SHA.

Use [`templates/release-readiness-record.md`](templates/release-readiness-record.md)
for every public release. A reviewer must confirm every applicable launch-gate
item and record an explicit approved, blocked, or rolled-back decision. Completed
records belong in the approved operational system and must not contain secrets.

## Read-only launch readiness report

Before using the authoritative launch gate, maintainers can inspect the current
repository/evidence status without contacting AWS:

```bash
python scripts/report-launch-readiness.py
python scripts/report-launch-readiness.py --json
```

The report reads the same manual evidence environment variables required by
`scripts/check-aws-launch-readiness.sh launch`, but it never provisions
infrastructure or authorizes spend.

Optionally, provide sanitized metadata that points to records held in the
approved operational system:

```bash
python scripts/report-launch-readiness.py \
  --evidence-metadata /secure/path/launch-evidence-metadata.json
```

Use `docs/templates/launch-evidence-metadata.example.json` only as a shape
example. Do not commit completed operational records, credentials, private
infrastructure identifiers, secret values, or customer data. Metadata is
traceability only: it does not satisfy a gate whose corresponding evidence
acknowledgment is incomplete.

A sanitized metadata record may also declare `review_after_days`. The readiness
report then shows whether that record is fresh or stale as of the current date,
or a deterministic date supplied with `--as-of-date YYYY-MM-DD`. No default
freshness period is invented by the repository: if `review_after_days` is
absent, freshness is reported as `not_evaluated`. Stale or malformed metadata
is advisory evidence for operator review and does not replace or alter the
authoritative launch gate.

To capture the exact sanitized readiness state for attachment to an approved
release record, write a local versioned snapshot:

```bash
python scripts/report-launch-readiness.py \
  --evidence-metadata /secure/path/launch-evidence-metadata.json \
  --release-sha 0123456789abcdef0123456789abcdef01234567 \
  --snapshot /secure/path/readiness-snapshot.json
```

The snapshot contains readiness status, missing/incomplete gate names, freshness
attention, sanitized record references, the review date, and the optional exact
release SHA. It deliberately omits evidence environment-variable names/values,
secrets, full operational records, and infrastructure details. Snapshot creation
is local and read-only and is not launch or spend authorization.

Each snapshot includes a deterministic SHA-256 checksum over its canonical
sanitized payload. Verify an archived snapshot locally with:

```bash
python scripts/report-launch-readiness.py \
  --verify-snapshot /secure/path/readiness-snapshot.json
```

A matching checksum shows that the snapshot content has not changed since the
checksum was created. It is **not** a digital signature, does not establish
operator identity or approval, and does not authorize a launch or infrastructure
spend. No signing keys or external verification service are introduced.

## Launch gate

Public traffic is not approved until all of these are true:

- the production media adapter uses private durable object storage and existing
  media has been copied and verified with `migrate-media-to-s3`;
- database point-in-time recovery and independent logical backups are enabled;
- media versioning and an independent media copy are enabled;
- a full restore rehearsal meets the documented RPO and RTO;
- the prior image and migration compatibility decision are recorded per release;
- backup failure alerts have an owner and tested notification path.
- `deployment-preflight` passes using the release image and production services.
