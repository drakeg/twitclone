#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RIPPLE_PORT="${RIPPLE_PORT:-8000}"
RIPPLE_BIND_HOST="${RIPPLE_BIND_HOST:-0.0.0.0}"
PILOT_DEMO_HEALTH_TIMEOUT="${PILOT_DEMO_HEALTH_TIMEOUT:-90}"
PILOT_DEMO_SKIP_BUILD="${PILOT_DEMO_SKIP_BUILD:-false}"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker is required for the Ripple pilot demo." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: Docker Compose v2 is required for the Ripple pilot demo." >&2
  exit 1
fi

compose=(docker compose)
if [[ "$PILOT_DEMO_SKIP_BUILD" == "true" ]]; then
  echo "Starting Ripple pilot demo with existing images..."
  "${compose[@]}" up -d
else
  echo "Building and starting Ripple pilot demo..."
  "${compose[@]}" up -d --build
fi

health_url="http://127.0.0.1:${RIPPLE_PORT}/health/ready"
deadline=$((SECONDS + PILOT_DEMO_HEALTH_TIMEOUT))

echo "Waiting for Ripple readiness at ${health_url}..."
until curl --fail --silent --show-error --max-time 3 "$health_url" >/dev/null 2>&1; do
  if (( SECONDS >= deadline )); then
    echo "ERROR: Ripple did not become ready within ${PILOT_DEMO_HEALTH_TIMEOUT}s." >&2
    "${compose[@]}" ps >&2 || true
    "${compose[@]}" logs --tail=80 web migrate >&2 || true
    exit 1
  fi
  sleep 2
done

echo "Seeding idempotent pilot demo content..."
"${compose[@]}" exec -T web flask --app application seed-demo-content

operator_path="/spaces/roadside-creators-club/operator"
operator_url="http://127.0.0.1:${RIPPLE_PORT}${operator_path}"

status="$(curl --silent --output /dev/null --write-out '%{http_code}' --max-time 5 "$operator_url")"
if [[ "$status" != "302" ]]; then
  echo "ERROR: Expected anonymous operator route request to return 302; got ${status}." >&2
  exit 1
fi

echo "Verifying authenticated owner workflow..."
cookie_jar="$(mktemp)"
login_page="$(mktemp)"
dashboard_page="$(mktemp)"
cleanup_demo_http_files() {
  rm -f "$cookie_jar" "$login_page" "$dashboard_page"
}
trap cleanup_demo_http_files EXIT

base_url="http://127.0.0.1:${RIPPLE_PORT}"
curl --fail --silent --show-error -c "$cookie_jar" "$base_url/login" -o "$login_page"
csrf_token="$(sed -n 's/.*name="csrf_token" value="\([^"]*\)".*/\1/p' "$login_page" | head -1)"
if [[ -z "$csrf_token" ]]; then
  echo "ERROR: Could not extract the login CSRF token from the Ripple login page." >&2
  exit 1
fi

login_status="$(
  curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
    -b "$cookie_jar" -c "$cookie_jar" \
    -X POST "$base_url/login" \
    --data-urlencode "email=campfirecode@example.test" \
    --data-urlencode "password=Passw0rd!" \
    --data-urlencode "csrf_token=$csrf_token"
)"
if [[ "$login_status" != "302" ]]; then
  echo "ERROR: Expected demo owner login to return 302; got ${login_status}." >&2
  exit 1
fi

dashboard_status="$(
  curl --silent --show-error --output "$dashboard_page" --write-out '%{http_code}' \
    -b "$cookie_jar" "$operator_url"
)"
if [[ "$dashboard_status" != "200" ]]; then
  echo "ERROR: Expected authenticated operator dashboard to return 200; got ${dashboard_status}." >&2
  exit 1
fi
if ! grep -q 'Community operating summary' "$dashboard_page"; then
  echo "ERROR: Operator dashboard did not render the expected summary." >&2
  exit 1
fi
if ! grep -q 'data-metric="member-count">8<' "$dashboard_page"; then
  echo "ERROR: Operator dashboard did not show the expected seeded 8-member community." >&2
  exit 1
fi

lan_ip=""
if command -v ipconfig >/dev/null 2>&1; then
  lan_ip="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
elif command -v hostname >/dev/null 2>&1; then
  lan_ip="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
fi
if [[ -z "$lan_ip" ]] && command -v ip >/dev/null 2>&1; then
  lan_ip="$(ip route get 1 2>/dev/null | awk '{for (i=1;i<=NF;i++) if ($i=="src") {print $(i+1); exit}}' || true)"
fi

echo
echo "Ripple pilot demo is ready."
echo "Local app: http://127.0.0.1:${RIPPLE_PORT}"
echo "Local operator dashboard: ${operator_url}"
if [[ "$RIPPLE_BIND_HOST" == "0.0.0.0" && -n "$lan_ip" ]]; then
  echo "LAN app: http://${lan_ip}:${RIPPLE_PORT}"
  echo "LAN operator dashboard: http://${lan_ip}:${RIPPLE_PORT}${operator_path}"
elif [[ "$RIPPLE_BIND_HOST" == "0.0.0.0" ]]; then
  echo "LAN binding is enabled; determine this host's LAN IP and use port ${RIPPLE_PORT}."
else
  echo "LAN access is disabled because RIPPLE_BIND_HOST=${RIPPLE_BIND_HOST}."
fi
echo "Demo owner: campfirecode@example.test"
echo "Demo moderator: bytebloom@example.test"
echo "Demo password: Passw0rd!"
echo
echo "Stop the demo with: docker compose down"
