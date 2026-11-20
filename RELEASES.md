# Releases and versioning

Ripple uses Semantic Versioning for published releases:

- **MAJOR** — incompatible public/API/deployment behavior requiring migration.
- **MINOR** — backward-compatible user-visible capability or substantial
  operational capability.
- **PATCH** — backward-compatible defect, security, dependency, or documentation
  correction when a release is justified.

A PR merge does not automatically create a release. Publish a GitHub release only
when a meaningful, tested state is ready for users/operators.

## Current release state

No published GitHub release is currently available. Do not add a dynamic release
badge or claim a release version until a real tag and GitHub release are
published.

## Release checklist

- Required CI checks are green.
- README badges accurately reflect the repository.
- SPRINTS.md and BACKLOG.md reflect completed/remaining work.
- User-visible or operator-visible changes are summarized.
- Migration/rollback guidance is updated when relevant.
- Security-sensitive changes are reviewed for secret exposure.
- A valid repository license has been intentionally selected before distributing
  under an open-source license claim.
- Version/tag selection is manually verified against compatibility impact.

Security fixes and urgent regressions may justify an expedited PATCH. Breaking
changes must include migration guidance and target a MAJOR release.
