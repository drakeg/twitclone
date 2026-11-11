#!/usr/bin/env bash
set -euo pipefail

: "${RIPPLE_DOMAIN:?Set RIPPLE_DOMAIN to the public Ripple hostname}"

SCHEME="${RIPPLE_SCHEME:-https}"
URL="${RIPPLE_STRIPE_WEBHOOK_URL:-${SCHEME}://${RIPPLE_DOMAIN}/billing/webhook}"
EXPECT_CONFIGURED="${RIPPLE_STRIPE_WEBHOOK_CONFIGURED:-true}"

case "${EXPECT_CONFIGURED}" in
  true|false) ;;
  *) echo "RIPPLE_STRIPE_WEBHOOK_CONFIGURED must be true or false." >&2; exit 2 ;;
esac

status="$(
  curl     --silent     --show-error     --output /dev/null     --write-out '%{http_code}'     --max-time "${RIPPLE_WEBHOOK_CHECK_TIMEOUT_SECONDS:-10}"     --request POST     --header 'Content-Type: application/json'     --header 'Stripe-Signature: t=0,v1=invalid-launch-reachability-probe'     --data '{}'     "${URL}"
)"

if [[ "${EXPECT_CONFIGURED}" == "true" ]]; then
  if [[ "${status}" != "400" ]]; then
    echo "Stripe webhook reachability check failed: expected HTTP 400 from a reachable, configured endpoint; got ${status}." >&2
    echo "URL: ${URL}" >&2
    exit 1
  fi
  echo "OK: Stripe webhook endpoint is reachable and rejects the invalid signature as expected (HTTP 400)."
else
  if [[ "${status}" != "400" && "${status}" != "503" ]]; then
    echo "Stripe webhook reachability check failed: expected HTTP 400 or 503 from the Ripple webhook route; got ${status}." >&2
    echo "URL: ${URL}" >&2
    exit 1
  fi
  echo "OK: Stripe webhook route is reachable (HTTP ${status}); configured processing was not required for this check."
fi
