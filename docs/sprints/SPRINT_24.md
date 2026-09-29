# Sprint 24 — Local Release-Image Serving Confidence

**Status:** Completed.

## Goal

Exercise Ripple's actual production web-serving entry point in CI while preserving the zero-spend deployment boundary.

## Story 24.1 — Immutable-image HTTP smoke

**Status:** Completed in PR #289.

- Keep the existing immutable local image build and revision-label verification.
- Replace the Python import-only smoke with an isolated launch of the image's default Gunicorn process.
- Poll `/health/live` from inside the running container without publishing a host port or joining an external network.
- Supply only a test-only secret and local test environment; do not require production secrets, PostgreSQL, migrations, or AWS.
- Bound startup retries; fail with container logs if the endpoint does not serve a successful health response.
- Always remove the temporary container.
- Preserve the separate production database-readiness, migration, preflight, and launch-gate contracts.

### Acceptance criteria

- CI fails when the image cannot start Gunicorn or answer `/health/live`.
- CI verifies HTTP status 200 and the `{"status": "ok"}` JSON response.
- Startup is bounded and container cleanup occurs on both success and failure.
- No host port, network egress, registry push, AWS API call, or new paid service is introduced.
- Automated contract tests cover CI invoking the smoke script and its isolation/cleanup behavior.
- Python, release-image, and Terraform validation remain separate jobs.

## Sprint outcome

Sprint 24 upgrades release-image validation from an import-only check to an actual HTTP-serving smoke test of the immutable runtime image's production Gunicorn entry point. CI now proves that the container can start, serve the documented database-independent liveness route, return the expected response, and clean itself up without exposing a host port or contacting external infrastructure.

The sprint deliberately stops at process/liveness confidence. Database readiness, schema migration, deployment preflight, restore rehearsal, TLS, and public-launch evidence remain separate operational contracts and are not implied by this smoke test.

## Definition of done

Completed. The immutable release image is exercised through its real Gunicorn serving path in CI, with bounded retries, isolated networking, cleanup, and zero-spend safeguards.

## Future direction

Expand local release verification only when a specific operational failure or readiness requirement justifies it. Liveness is not proof of database readiness or public launch authorization.
