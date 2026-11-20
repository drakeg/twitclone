# Agent operating instructions

These instructions apply to this repository and supplement the centralized
`drakeg/madmallard-repository-standards` guidance. Project-specific security,
architecture, deployment, and product requirements take precedence when they are
stricter.

## Operating model

1. Work in small, reviewable branches and pull requests.
2. Follow Build → Deploy/Test → Fix → Retest → Continue. Do not stop merely
   because a sprint, PR, or fix completes when another ready task exists.
3. Treat failed CI, tests, builds, deployment checks, accessibility regressions,
   and security findings as P0/P1 work until understood.
4. Keep README, SPRINTS.md, BACKLOG.md, RELEASES.md, CONTRIBUTING.md, SECURITY.md,
   and the detailed docs under `docs/` aligned with code changes.
5. Preserve Ripple's established roadmap history. Do not invent a new numbered
   sprint merely to satisfy process documentation; root SPRINTS.md summarizes
   current operating work and links the authoritative roadmap.
6. Never claim a test, deployment, customer result, market validation, release,
   or security status that was not actually verified.
7. Never create paid AWS resources or authorize spend without explicit approval.
   Issue #16 and the Terraform configuration do not constitute spend approval.
8. Keep this repository independent. Do not connect databases, authentication,
   services, or deployment state to unrelated projects without explicit
   instruction.

## Testing and deployment

- Local development uses Docker Compose and publishes on `0.0.0.0` by default
  for LAN testing.
- Run the full test suite with `docker compose run --rm test` when a compatible
  local Docker environment is available.
- GitHub CI is the authoritative remote validation for Python, release-image,
  repository-standards, and Terraform checks.
- Production activation remains separately gated by
  `scripts/check-aws-launch-readiness.sh launch`.
- Fix CI failures on the current PR branch before starting unrelated work.

## README badges

- Keep the managed badge block immediately below the first README H1.
- Derive technology/version claims from repository configuration only.
- Use the official dynamic GitHub Actions badge for CI and dynamic issue/PR
  badges.
- Do not add a release badge until a published GitHub release exists.
- Do not add a license badge until the repository owner selects a valid license.
- Run `python scripts/check_repository_standards.py` in CI whenever badge,
  workflow, licensing, or governance files change.

## Commercialization

Ripple should be evaluated as a potential paid product, but demand must not be
invented. Prioritize an SMB/community-management wedge that can be validated
quickly, focusing on measurable customer value such as reduced community
administration time, member engagement, or paid membership management.
Commercialization work must preserve existing security, moderation,
accessibility, and privacy boundaries.

## Pull request updates

Progress updates should include what changed, validation status, the direct PR
link, blockers, and the next ready priority. Respect branch protections and
required reviews.
