#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${RIPPLE_ENV_FILE:-/tmp/ripple-production-dry-run.env}"
COMPOSE_FILE="${RIPPLE_PRODUCTION_COMPOSE:-${ROOT_DIR}/compose.production.yaml}"

cleanup() {
  if [[ "${RIPPLE_DRY_RUN_KEEP_ENV:-false}" != "true" ]]; then
    rm -f "${ENV_FILE}"
  fi
}
trap cleanup EXIT

: "${RIPPLE_IMAGE:?Set RIPPLE_IMAGE to the immutable image that would be released}"
: "${RIPPLE_DOMAIN:=ripple.invalid}"
: "${RIPPLE_TLS_EMAIL:=operator@ripple.invalid}"

if [[ "${RIPPLE_IMAGE}" == *":latest" ]]; then
  echo "RIPPLE_IMAGE must be immutable; :latest is not accepted." >&2
  exit 1
fi

export TWITCLONE_ENV="${TWITCLONE_ENV:-production}"
export SECRET_KEY="${SECRET_KEY:-dry-run-only-not-a-production-secret}"
export DATABASE_URL="${DATABASE_URL:-postgresql://ripple:dry-run@database.invalid:5432/ripple}"
export MEDIA_STORAGE_BACKEND="${MEDIA_STORAGE_BACKEND:-s3}"
export MEDIA_S3_BUCKET="${MEDIA_S3_BUCKET:-ripple-dry-run-private-bucket}"
export MEDIA_S3_REGION="${MEDIA_S3_REGION:-us-east-1}"
export MEDIA_S3_PREFIX="${MEDIA_S3_PREFIX:-media}"
export SCHEDULER_ENABLED="${SCHEDULER_ENABLED:-false}"
export SCHEDULER_INTERVAL_SECONDS="${SCHEDULER_INTERVAL_SECONDS:-60}"
export STRIPE_BILLING_ENABLED="${STRIPE_BILLING_ENABLED:-false}"
export RIPPLE_CONFIG_SOURCE=env
export RIPPLE_ENV_FILE="${ENV_FILE}"
export RIPPLE_DOMAIN RIPPLE_TLS_EMAIL

bash "${ROOT_DIR}/scripts/render-production-env.sh"

echo "[1/5] Runtime configuration rendered and validated: ${ENV_FILE}"
RIPPLE_ENV_FILE="${ENV_FILE}" RIPPLE_PRODUCTION_COMPOSE="${COMPOSE_FILE}" \
  bash "${ROOT_DIR}/scripts/deploy-production.sh" validate

echo "[2/5] Production Compose contract is valid."
echo "[3/5] Release image selected: ${RIPPLE_IMAGE}"
echo "[4/5] Planned live sequence: pull image -> migrate -> deployment-preflight -> web/worker -> HTTPS proxy -> health/manual verification."
echo "[5/5] Planned rollback: set PREVIOUS_RIPPLE_IMAGE and run deploy-production.sh rollback; database migrations are never auto-downgraded."
echo
echo "DRY RUN COMPLETE: no containers were started, no image was pulled, no migration/preflight was executed, Terraform was not invoked, and no AWS resource was created."
