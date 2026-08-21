# ADR-0037: Private S3-compatible production media

- Status: Accepted
- Date: 2026-08-20
- Sprint: 6
- Story: 6.5

## Context

Uploaded images were written directly to one local directory and served from
that filesystem. This works for local Compose but loses data on ephemeral
production containers and cannot be shared safely by multiple instances.

## Decision

- Keep filesystem media as the zero-configuration local and test adapter.
- Require a private S3-compatible bucket in production.
- Preserve generated filenames, database columns, templates, and
  `/uploads/<filename>` URLs.
- Proxy thumbnail and profile-banner reads through Ripple so the bucket needs no
  public object access; original images are not exposed by the media route.
- Reject path components before storage access.
- Delete partially written original/thumbnail pairs when storage fails.
- Use Boto3's standard credential chain so secrets remain platform-owned.

## Consequences

- Ephemeral production containers no longer own durable media.
- Media reads consume an application request and memory proportional to object
  size; a later measured optimization may use short-lived signed URLs.
- Existing filesystem media requires an explicit verified copy before cutover.
- Local Compose and its isolated test command remain unchanged.
