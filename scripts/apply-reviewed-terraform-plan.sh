#!/usr/bin/env bash
set -euo pipefail

: "${RIPPLE_AWS_SPEND_AUTHORIZED:?Set RIPPLE_AWS_SPEND_AUTHORIZED=true only after explicit spend authorization}"
: "${RIPPLE_REVIEWED_PLAN:?Set RIPPLE_REVIEWED_PLAN to the reviewed Terraform binary plan}"
: "${RIPPLE_REVIEWED_PLAN_SHA256:?Set RIPPLE_REVIEWED_PLAN_SHA256 to the recorded SHA-256 of that plan}"

if [[ "${RIPPLE_AWS_SPEND_AUTHORIZED}" != "true" ]]; then
  echo "BLOCKED: explicit AWS spend authorization is required." >&2
  exit 1
fi

[[ -f "${RIPPLE_REVIEWED_PLAN}" ]] || {
  echo "BLOCKED: reviewed Terraform plan not found: ${RIPPLE_REVIEWED_PLAN}" >&2
  exit 1
}

for command in terraform sha256sum; do
  command -v "${command}" >/dev/null 2>&1 || {
    echo "Required command not found: ${command}" >&2
    exit 1
  }
done

actual_sha="$(sha256sum "${RIPPLE_REVIEWED_PLAN}" | awk '{print $1}')"
if [[ "${actual_sha}" != "${RIPPLE_REVIEWED_PLAN_SHA256}" ]]; then
  echo "BLOCKED: reviewed Terraform plan checksum does not match." >&2
  exit 1
fi

echo "Applying the exact reviewed Terraform plan..."
terraform apply "${RIPPLE_REVIEWED_PLAN}"

echo "Verifying idempotence with a fresh plan..."
set +e
terraform plan -detailed-exitcode -out=/tmp/ripple-idempotence.tfplan
status=$?
set -e

case "${status}" in
  0)
    echo "OK: re-plan returned no changes; Terraform apply is idempotent for the current inputs/state."
    ;;
  2)
    echo "BLOCKED: re-plan contains changes after apply; investigate before declaring infrastructure ready." >&2
    exit 1
    ;;
  *)
    echo "BLOCKED: Terraform re-plan failed with exit code ${status}." >&2
    exit "${status}"
    ;;
esac

echo "This script requires prior spend authorization; it does not grant authorization itself."
