#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${RIPPLE_ENV_FILE:-/etc/ripple/ripple.env}"
SOURCE="${RIPPLE_CONFIG_SOURCE:-shell}"
PARAMETER_PATH="${RIPPLE_PARAMETER_PATH:-/ripple/production}"

required=(TWITCLONE_ENV SECRET_KEY DATABASE_URL MEDIA_STORAGE_BACKEND MEDIA_S3_BUCKET MEDIA_S3_REGION MEDIA_S3_PREFIX SCHEDULER_ENABLED SCHEDULER_INTERVAL_SECONDS STRIPE_BILLING_ENABLED)
optional=(STRIPE_SECRET_KEY STRIPE_WEBHOOK_SECRET)

load_parameter_store() {
  command -v aws >/dev/null 2>&1 || { echo "aws CLI is required for RIPPLE_CONFIG_SOURCE=ssm" >&2; exit 1; }
  local payload
  payload="$(aws ssm get-parameters-by-path --path "${PARAMETER_PATH}" --with-decryption --recursive --query 'Parameters[*].[Name,Value]' --output text)"
  while IFS=$'\t' read -r name value; do
    [[ -z "${name}" ]] && continue
    key="${name##*/}"
    case "${key}" in
      TWITCLONE_ENV|SECRET_KEY|DATABASE_URL|MEDIA_STORAGE_BACKEND|MEDIA_S3_BUCKET|MEDIA_S3_REGION|MEDIA_S3_PREFIX|SCHEDULER_ENABLED|SCHEDULER_INTERVAL_SECONDS|STRIPE_BILLING_ENABLED|STRIPE_SECRET_KEY|STRIPE_WEBHOOK_SECRET)
        printf -v "${key}" '%s' "${value}"
        export "${key}"
        ;;
    esac
  done <<< "${payload}"
}

validate_value() {
  local key="$1" value="${!1:-}"
  if [[ -z "${value}" ]]; then
    echo "Required production setting is missing: ${key}" >&2
    exit 1
  fi
  if [[ "${value}" == *$'\n'* || "${value}" == *$'\r'* ]]; then
    echo "Production setting ${key} contains a newline and cannot be written safely." >&2
    exit 1
  fi
}

case "${SOURCE}" in
  shell) ;;
  ssm) load_parameter_store ;;
  *) echo "RIPPLE_CONFIG_SOURCE must be shell or ssm." >&2; exit 1 ;;
esac

for key in "${required[@]}"; do validate_value "${key}"; done

if [[ "${STRIPE_BILLING_ENABLED}" == "true" ]]; then
  validate_value STRIPE_SECRET_KEY
  validate_value STRIPE_WEBHOOK_SECRET
fi

umask 077
mkdir -p "$(dirname "${OUTPUT_FILE}")"
tmp="$(mktemp "${OUTPUT_FILE}.tmp.XXXXXX")"
trap 'rm -f "${tmp}"' EXIT

for key in "${required[@]}" "${optional[@]}"; do
  value="${!key:-}"
  printf '%s=%q\n' "${key}" "${value}" >> "${tmp}"
done

chmod 600 "${tmp}"
mv "${tmp}" "${OUTPUT_FILE}"
trap - EXIT
printf 'Wrote production runtime configuration to %s with mode 0600.\n' "${OUTPUT_FILE}"
