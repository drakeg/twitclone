#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-structure}"

fail() { echo "BLOCKED: $*" >&2; exit 1; }
pass() { echo "OK: $*"; }
require_file() { [[ -f "$1" ]] || fail "Required file missing: $1"; }
require_true() { [[ "${!1:-}" == "true" ]] || fail "$1=true is required in launch mode"; }

case "$MODE" in
  structure|launch) ;;
  *) fail "Usage: scripts/check-aws-launch-readiness.sh {structure|launch}" ;;
esac

cd "$ROOT_DIR"

for file in \
  compose.production.yaml \
  deploy/bootstrap-host.sh \
  deploy/Caddyfile \
  deploy/env.production.example \
  scripts/build-release-image.sh \
  scripts/render-production-env.sh \
  scripts/deploy-production.sh \
  scripts/dry-run-production-release.sh \
  infra/terraform/main.tf \
  infra/terraform/variables.tf \
  infra/terraform/outputs.tf \
  docs/operations.md \
  docs/templates/release-readiness-record.md \
  docs/templates/restore-rehearsal-record.md; do
  require_file "$file"
done
pass "required production artifacts are present"

if command -v terraform >/dev/null 2>&1; then
  (
    cd infra/terraform
    terraform fmt -check >/dev/null
    terraform init -backend=false -input=false >/dev/null
    terraform validate >/dev/null
  )
  pass "Terraform formatting and validation passed"
else
  fail "Terraform is required for the readiness gate"
fi

if grep -R -nE 'terraform[[:space:]]+apply|aws[[:space:]].*(create|run-instances|put-parameter)' \
    scripts/check-aws-launch-readiness.sh scripts/dry-run-production-release.sh scripts/deploy-production.sh >/dev/null; then
  fail "readiness/dry-run scripts must not contain infrastructure-creation commands"
fi
pass "readiness path contains no Terraform apply or AWS create commands"

DRY_IMAGE="${RIPPLE_IMAGE:-ripple:0123456789abcdef0123456789abcdef01234567}"
RIPPLE_IMAGE="$DRY_IMAGE" bash scripts/dry-run-production-release.sh >/dev/null
pass "production release dry run passed"

if [[ "$MODE" == "structure" ]]; then
  echo
  echo "STRUCTURE READY: repository-side AWS launch contracts validate without provisioning infrastructure."
  echo "This is not spend authorization and does not mean the public-launch evidence gate is complete."
  exit 0
fi

[[ -z "$(git status --porcelain)" ]] || fail "launch mode requires a clean Git checkout"
[[ "$(git rev-parse --abbrev-ref HEAD)" == "main" ]] || fail "launch mode requires main"
HEAD_SHA="$(git rev-parse HEAD)"
[[ "$HEAD_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "unable to resolve an exact Git SHA"

: "${RIPPLE_RELEASE_SHA:?Set RIPPLE_RELEASE_SHA to the exact release Git SHA}"
: "${RIPPLE_IMAGE:?Set RIPPLE_IMAGE to the immutable release image reference}"
: "${RIPPLE_HOST_BOOTSTRAP_REF:?Set RIPPLE_HOST_BOOTSTRAP_REF to the exact deployment-artifact Git SHA}"

[[ "$RIPPLE_RELEASE_SHA" == "$HEAD_SHA" ]] || fail "RIPPLE_RELEASE_SHA must equal current main HEAD ($HEAD_SHA)"
[[ "$RIPPLE_HOST_BOOTSTRAP_REF" =~ ^[0-9a-f]{40}$ ]] || fail "RIPPLE_HOST_BOOTSTRAP_REF must be a 40-character SHA"
[[ "$RIPPLE_HOST_BOOTSTRAP_REF" == "$RIPPLE_RELEASE_SHA" ]] || fail "bootstrap and release refs must match for initial launch"
[[ "$RIPPLE_IMAGE" != *":latest" ]] || fail "RIPPLE_IMAGE may not use :latest"
[[ "$RIPPLE_IMAGE" == *"$RIPPLE_RELEASE_SHA"* || "$RIPPLE_IMAGE" == *@sha256:* ]] || fail "RIPPLE_IMAGE must identify the release SHA or an immutable digest"

require_true RIPPLE_COST_REVIEWED
require_true RIPPLE_RESTORE_REHEARSAL_PASSED
require_true RIPPLE_ACCESSIBILITY_EVIDENCE_PASSED
require_true RIPPLE_BACKUP_ALERT_PATH_TESTED
require_true RIPPLE_RELEASE_RECORD_PREPARED

: "${RIPPLE_COST_REVIEW_DATE:?Set RIPPLE_COST_REVIEW_DATE (YYYY-MM-DD)}"
[[ "$RIPPLE_COST_REVIEW_DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || fail "RIPPLE_COST_REVIEW_DATE must be YYYY-MM-DD"

pass "clean main checkout and immutable release identifiers confirmed"
pass "cost review, restore rehearsal, accessibility evidence, backup alert path, and release record are acknowledged"

echo
echo "LAUNCH GATE READY: repository and evidence prerequisites are satisfied."
echo "This script still does not run terraform plan/apply and does not authorize AWS spend."
