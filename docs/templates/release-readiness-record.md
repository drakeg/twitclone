# Ripple release readiness record

Copy this template into the approved operational record system for each public
release. Do not commit completed records, credentials, secret values, database
URLs, customer data, or private infrastructure details to this repository.

## Release identity

- Release SHA:
- Previous known-good SHA:
- Operator:
- Reviewer/approver:
- Planned traffic-enable time (UTC):
- Production environment/provider:
- Change or incident reference:

## Immutable artifacts and compatibility

- [ ] Release image is tagged with the release SHA.
- [ ] Release image digest is recorded:
- [ ] Previous image and digest are retained.
- [ ] Migration compatibility decision is recorded: backward compatible / forward fix required / restore required
- Migration head(s):

## Recovery set

- Database backup identifier:
- Database backup checksum and UTC completion time:
- Media backup identifier:
- Media object count and total bytes:
- Media backup UTC completion time:
- Retention expiry:
- [ ] Database point-in-time recovery is healthy.
- [ ] Media versioning is enabled.
- [ ] Independent database and media copies are verified.

## Restore rehearsal

- Rehearsal record location:
- Rehearsal date (UTC):
- Observed recovery point (RPO):
- Observed recovery time (RTO):
- [ ] Rehearsal used isolated database and media resources.
- [ ] Rehearsal met the current RPO and RTO targets.
- [ ] Rehearsal discrepancies have owners and dispositions.

## Release execution

- Migration job identifier and result:
- Media migration result, if required:
- Deployment preflight job identifier and result:
- `/health/live` result and UTC time:
- `/health/ready` result and UTC time:
- Login/timeline/media smoke-test result:
- Scheduled-worker result:
- [ ] Exactly one scheduled worker is running.
- [ ] No public traffic was enabled before migration and preflight passed.

## Monitoring, alerts, and cost

- Log/monitoring dashboard location:
- Backup-failure alert owner:
- Backup-failure alert test date and result:
- Approved monthly cost range:
- Budget-alert thresholds and owner:
- [ ] Current provider prices were rechecked before provisioning.

## Decision

- Result: approved / blocked / rolled back
- Traffic enabled or rollback started (UTC):
- Decision maker:
- Blocking findings or rollback reason:
- Follow-up work and owners:
