#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if ! command -v git >/dev/null 2>&1 || ! command -v docker >/dev/null 2>&1; then
  echo "git and docker are required." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" && "${ALLOW_DIRTY_RELEASE_BUILD:-false}" != "true" ]]; then
  echo "Refusing release image build from a dirty checkout. Commit/stash changes or set ALLOW_DIRTY_RELEASE_BUILD=true for local experimentation only." >&2
  exit 1
fi

GIT_SHA="${RIPPLE_RELEASE_SHA:-$(git rev-parse HEAD)}"
SHORT_SHA="${GIT_SHA:0:12}"
SOURCE_URL="${RIPPLE_SOURCE_URL:-https://github.com/drakeg/twitclone}"
IMAGE_REPOSITORY="${RIPPLE_IMAGE_REPOSITORY:-ripple}"
IMAGE_REF="${RIPPLE_IMAGE_REF:-${IMAGE_REPOSITORY}:${SHORT_SHA}}"
CREATED="${RIPPLE_BUILD_CREATED:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
PUSH="${RIPPLE_PUSH_IMAGE:-false}"
PLATFORM="${RIPPLE_BUILD_PLATFORM:-linux/arm64}"

if [[ "${IMAGE_REF}" == *":latest" ]]; then
  echo "Release image must be immutable; :latest is not allowed." >&2
  exit 1
fi

BUILD_ARGS=(
  --platform "${PLATFORM}"
  --build-arg "RIPPLE_BUILD_REVISION=${GIT_SHA}"
  --build-arg "RIPPLE_BUILD_SOURCE=${SOURCE_URL}"
  --build-arg "RIPPLE_BUILD_CREATED=${CREATED}"
  -t "${IMAGE_REF}"
  .
)

echo "Building ${IMAGE_REF} for ${PLATFORM} from ${GIT_SHA}"
docker build "${BUILD_ARGS[@]}"

actual_revision="$(docker image inspect "${IMAGE_REF}" --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}')"
if [[ "${actual_revision}" != "${GIT_SHA}" ]]; then
  echo "Built image revision label mismatch: expected ${GIT_SHA}, got ${actual_revision}" >&2
  exit 1
fi

image_id="$(docker image inspect "${IMAGE_REF}" --format '{{.Id}}')"
echo "Verified image: ${IMAGE_REF}"
echo "Image ID: ${image_id}"
echo "Revision: ${actual_revision}"

if [[ "${PUSH}" == "true" ]]; then
  if [[ "${IMAGE_REF}" != *"/"* ]]; then
    echo "RIPPLE_PUSH_IMAGE=true requires a registry-qualified RIPPLE_IMAGE_REF." >&2
    exit 1
  fi
  docker push "${IMAGE_REF}"
  echo "Published ${IMAGE_REF}. Record the registry digest and use that digest for production deployment when available."
else
  echo "Image publication skipped (default). No registry or AWS service was contacted."
fi

cat <<EOF

Use locally with the production deployment model by setting:
  export RIPPLE_IMAGE='${IMAGE_REF}'

Publishing is opt-in only:
  RIPPLE_IMAGE_REF='<registry>/ripple:${SHORT_SHA}' RIPPLE_PUSH_IMAGE=true scripts/build-release-image.sh
EOF
