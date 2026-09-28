#!/usr/bin/env bash
# Exercise the actual Gunicorn process in an immutable local release image.
set -euo pipefail

if [[ $# -ne 1 || -z "$1" ]]; then
  echo "Usage: $0 <local-image-reference>" >&2
  exit 2
fi

image="$1"
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for the release-image HTTP smoke test." >&2
  exit 2
fi

container_id=""
cleanup() {
  if [[ -n "$container_id" ]]; then
    docker rm -f "$container_id" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

# No host port, registry interaction, AWS credentials, or external container network.
container_id="$(docker run --detach --rm --network none \
  -e TWITCLONE_ENV=testing \
  -e SECRET_KEY=ci-test-only-secret \
  -e DATABASE_URL=sqlite:///:memory: \
  -e SCHEDULER_ENABLED=false \
  "$image")"

for attempt in {1..30}; do
  if docker exec "$container_id" python -c '
import json
import urllib.request
with urllib.request.urlopen("http://127.0.0.1:8000/health/live", timeout=2) as response:
    assert response.status == 200
    assert json.load(response) == {"status": "ok"}
' >/dev/null 2>&1; then
    echo "Release image serves /health/live over its production Gunicorn entry point."
    exit 0
  fi
  sleep 1
done

echo "Release image did not serve /health/live within the smoke-test retry budget." >&2
docker logs "$container_id" >&2 || true
exit 1
