# ADR-0038: Repeatable media migration command

- Status: Accepted
- Date: 2026-08-20
- Sprint: 6
- Story: 6.6

## Context

The S3 media adapter makes new production uploads durable, but existing
filesystem uploads still need a safe cutover path. An ordinary recursive bucket
copy does not share Ripple's configured object prefix, credential path, or
application-level verification behavior.

## Decision

- Provide `flask --app application migrate-media-to-s3` as the supported
  filesystem-to-S3 migration command.
- Require the configured S3 adapter so the command uses the same bucket,
  endpoint, region, prefix, and credential chain as the application.
- Support a dry run before writes and make identical repeat runs no-ops.
- Compare source and destination content using SHA-256 and read every newly
  written object back for verification.
- Refuse differing destination objects unless an operator explicitly supplies
  `--overwrite` after review.
- Ignore directories, hidden files, and symbolic links; preserve each accepted
  source filename as its object name.

## Consequences

- Operators have a documented, auditable migration path before production
  cutover.
- The command reads each source and destination object into memory; this is
  appropriate for Ripple's image-size contract but is not a bulk-transfer tool
  for arbitrary large objects.
- Local development and `docker compose run --rm test` remain filesystem-backed
  and unchanged.
