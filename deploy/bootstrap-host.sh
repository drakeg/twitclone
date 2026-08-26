#!/usr/bin/env bash
set -euo pipefail

RIPPLE_ROOT="${RIPPLE_ROOT:-/opt/ripple}"
RIPPLE_STATE_DIR="${RIPPLE_STATE_DIR:-/var/lib/ripple}"
RIPPLE_DEPLOYMENT_REF="${RIPPLE_DEPLOYMENT_REF:-}"
RIPPLE_REPOSITORY_ARCHIVE_BASE="${RIPPLE_REPOSITORY_ARCHIVE_BASE:-https://github.com/drakeg/twitclone/archive}"
DOCKER_COMPOSE_VERSION="${DOCKER_COMPOSE_VERSION:-5.4.0}"
DOCKER_COMPOSE_AARCH64_SHA256="${DOCKER_COMPOSE_AARCH64_SHA256:-fc5d1371f1ec7987e703da94ede49af3fbfb240b83f22991a98511de7bc4b93b}"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

[[ "${EUID}" -eq 0 ]] || fail "bootstrap-host.sh must run as root"
[[ "${RIPPLE_DEPLOYMENT_REF}" =~ ^[0-9a-fA-F]{40}$ ]] || fail "RIPPLE_DEPLOYMENT_REF must be an immutable 40-character Git commit SHA"

if [[ ! -r /etc/os-release ]]; then
  fail "/etc/os-release is required"
fi
# shellcheck disable=SC1091
source /etc/os-release
[[ "${ID:-}" == "amzn" && "${VERSION_ID:-}" == "2023" ]] || fail "This bootstrap supports Amazon Linux 2023 only"

export LANG=C.UTF-8

dnf install -y docker curl tar gzip
systemctl enable --now docker

if id ec2-user >/dev/null 2>&1; then
  usermod -a -G docker ec2-user
fi

compose_plugin_dir="/usr/local/libexec/docker/cli-plugins"
compose_plugin="${compose_plugin_dir}/docker-compose"
mkdir -p "${compose_plugin_dir}"

installed_compose_version=""
if [[ -x "${compose_plugin}" ]]; then
  installed_compose_version="$(${compose_plugin} version --short 2>/dev/null || true)"
  installed_compose_version="${installed_compose_version#v}"
fi

if [[ "${installed_compose_version}" != "${DOCKER_COMPOSE_VERSION}" ]]; then
  tmp_compose="$(mktemp)"
  trap 'rm -f "${tmp_compose:-}" "${archive_file:-}"' EXIT
  curl --fail --location --silent --show-error \
    "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-linux-aarch64" \
    --output "${tmp_compose}"
  echo "${DOCKER_COMPOSE_AARCH64_SHA256}  ${tmp_compose}" | sha256sum --check --status \
    || fail "Docker Compose checksum verification failed"
  install -m 0755 "${tmp_compose}" "${compose_plugin}"
fi

docker compose version

mkdir -p "${RIPPLE_ROOT}/deploy" "${RIPPLE_ROOT}/scripts" "${RIPPLE_STATE_DIR}" /etc/ripple
chmod 0755 "${RIPPLE_ROOT}" "${RIPPLE_ROOT}/deploy" "${RIPPLE_ROOT}/scripts" "${RIPPLE_STATE_DIR}"
chmod 0700 /etc/ripple

archive_file="$(mktemp --suffix=.tar.gz)"
archive_url="${RIPPLE_REPOSITORY_ARCHIVE_BASE}/${RIPPLE_DEPLOYMENT_REF}.tar.gz"
curl --fail --location --silent --show-error "${archive_url}" --output "${archive_file}"

extract_dir="$(mktemp -d)"
trap 'rm -rf "${extract_dir:-}"; rm -f "${tmp_compose:-}" "${archive_file:-}"' EXIT
tar -xzf "${archive_file}" -C "${extract_dir}"
source_dir="$(find "${extract_dir}" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
[[ -n "${source_dir}" ]] || fail "Could not locate extracted Ripple deployment source"

install -m 0644 "${source_dir}/compose.production.yaml" "${RIPPLE_ROOT}/compose.production.yaml"
install -m 0644 "${source_dir}/deploy/Caddyfile" "${RIPPLE_ROOT}/deploy/Caddyfile"
install -m 0644 "${source_dir}/deploy/env.production.example" "${RIPPLE_ROOT}/deploy/env.production.example"
install -m 0755 "${source_dir}/scripts/deploy-production.sh" "${RIPPLE_ROOT}/scripts/deploy-production.sh"

cat > "${RIPPLE_STATE_DIR}/bootstrap.env" <<EOF
RIPPLE_DEPLOYMENT_REF=${RIPPLE_DEPLOYMENT_REF}
DOCKER_COMPOSE_VERSION=${DOCKER_COMPOSE_VERSION}
EOF
chmod 0644 "${RIPPLE_STATE_DIR}/bootstrap.env"

touch "${RIPPLE_STATE_DIR}/bootstrap-complete"

echo "Ripple container host bootstrap complete for deployment ref ${RIPPLE_DEPLOYMENT_REF}."
echo "No application secrets were created. Populate /etc/ripple/ripple.env separately before deployment."
