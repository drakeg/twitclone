# Ripple restore rehearsal record

Copy this template into the approved operational record system for every
rehearsal. Never include credentials, secret values, database URLs, customer
data, or private infrastructure details in a repository or broadly shared log.

## Rehearsal identity

- Exercise date (UTC):
- Operator:
- Reviewer:
- Release SHA and image digest:
- Source recovery-set identifier:
- Scenario exercised:

## Source recovery point

- Database backup identifier and checksum:
- Database backup completion time (UTC):
- Media backup identifier:
- Media backup completion time (UTC):
- Expected migration head(s):
- Expected database row-count sample:
- Expected media object count and total bytes:

## Isolated restore

- Restore start time (UTC):
- Isolated database reference:
- Isolated private media reference:
- Database restore completion time (UTC):
- Media restore completion time (UTC):
- Application start time (UTC):
- [ ] No production database or live media bucket was targeted.
- [ ] Public listing and public traffic remained disabled.

## Verification evidence

- `flask --app application db current` result:
- `flask --app application deployment-preflight` result:
- `/health/live` result:
- `/health/ready` result:
- Login and timeline result:
- Representative image retrieval result:
- Database row-count comparison:
- Media object-count and byte comparison:
- Relationship/billing sample result:
- Scheduled-worker result:

## Recovery objectives

- Restore validation completed (UTC):
- Observed RPO:
- RPO target: 24 hours or less for independent backups
- RPO met: yes / no
- Observed RTO:
- RTO target: four hours or less in the supported response window
- RTO met: yes / no

## Findings and disposition

- Missing or inconsistent data:
- Reconciliation required:
- Security or access findings:
- Performance or capacity findings:
- Follow-up work, owners, and due dates:
- Exercise result: passed / failed
- Reviewer approval:

## Cleanup

- Evidence saved and reviewed (UTC):
- Isolated application stopped (UTC):
- Isolated database disposal reference:
- Isolated media disposal reference:
- [ ] Temporary resources were destroyed only after evidence was retained.
