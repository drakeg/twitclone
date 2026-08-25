#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${RIPPLE_PRODUCTION_COMPOSE:-${ROOT_DIR}/compose.production.yaml}"
ENV_FILE="${RIPPLE_ENV_FILE:-/etc/ripple/ripple.env}"
ACTION="${1:-help}"

compose() {
  RIPPLE_ENV_FILE="${ENV_FILE}" docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" "$@"
}

require_file() {
  if [[ ! -f "$1" ]]; then
    echo "Required file not found: $1" >&2
    exit 1
  fi
}

require_release_inputs() {
  require_file "${ENV_FILE}"
  : "${RIPPLE_IMAGE:?Set RIPPLE_IMAGE to the immutable release image reference}"
  : "${RIPPLE_DOMAIN:?Set RIPPLE_DOMAIN to the public hostname}"
  : "${RIPPLE_TLS_EMAIL:?Set RIPPLE_TLS_EMAIL for TLS certificate notices}"

  if [[ "${RIPPLE_IMAGE}" == *":latest" ]]; then
    echo "RIPPLE_IMAGE must be immutable; the :latest tag is not allowed." >&2
    exit 1
  fi
}

validate() {
  require_release_inputs
  compose config --quiet
  echo "Production Compose configuration is valid."
}

deploy() {
  require_release_inputs
  compose config --quiet
  compose pull
  compose run --rm migrate
  compose run --rm preflight
  compose up -d --no-deps web worker
  compose up -d proxy
  compose ps
  echo "Deployment started from ${RIPPLE_IMAGE}. Verify HTTPS, /health/live, /health/ready, login, timeline, media, worker logs, and Stripe webhook reachability before recording release approval."
}

rollback() {
  require_file "${ENV_FILE}"
  : "${PREVIOUS_RIPPLE_IMAGE:?Set PREVIOUS_RIPPLE_IMAGE to the previous known-good immutable image}"
  if [[ "${PREVIOUS_RIPPLE_IMAGE}" == *":latest" ]]; then
    echo "PREVIOUS_RIPPLE_IMAGE must be immutable; the :latest tag is not allowed." >&2
    exit 1
  fi
  export RIPPLE_IMAGE="${PREVIOUS_RIPPLE_IMAGE}"
  require_release_inputs
  compose pull
  compose up -d --no-deps web worker
  compose up -d proxy
  compose ps
  echo "Application containers rolled back to ${PREVIOUS_RIPPLE_IMAGE}. The database was not downgraded. Complete the rollback checks in docs/operations.md."
}

case "${ACTION}" in
  validate) validate ;;
  deploy) deploy ;;
  rollback) rollback ;;
  status)
    require_file "${ENV_FILE}"
    compose ps
    ;;
  *)
    cat <<'EOF'
Usage: scripts/deploy-production.sh {validate|deploy|rollback|status}

Required environment for validate/deploy:
  RIPPLE_IMAGE       Immutable Ripple image tag or digest (never :latest)
  RIPPLE_DOMAIN      Public hostname
  RIPPLE_TLS_EMAIL   Certificate notification address

Optional:
  RIPPLE_ENV_FILE             Defaults to /etc/ripple/ripple.env
  RIPPLE_PRODUCTION_COMPOSE   Defaults to compose.production.yaml

Rollback additionally requires PREVIOUS_RIPPLE_IMAGE.

This script manages containers only. It never runs Terraform and never creates AWS infrastructure.
EOF
    ;;
esac
