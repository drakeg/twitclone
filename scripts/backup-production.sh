#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?Set DATABASE_URL to the production PostgreSQL connection string}"
: "${MEDIA_S3_BUCKET:?Set MEDIA_S3_BUCKET to the live production media bucket}"
: "${RIPPLE_BACKUP_DIR:?Set RIPPLE_BACKUP_DIR to a protected local staging directory}"
: "${RIPPLE_BACKUP_ENCRYPTION_PASSPHRASE:?Set RIPPLE_BACKUP_ENCRYPTION_PASSPHRASE from a secure runtime source}"
: "${RIPPLE_MEDIA_BACKUP_DESTINATION:?Set RIPPLE_MEDIA_BACKUP_DESTINATION to an independent s3:// bucket or prefix}"

for command in pg_dump pg_restore openssl sha256sum aws; do
  command -v "${command}" >/dev/null 2>&1 || {
    echo "Required command not found: ${command}" >&2
    exit 1
  }
done

case "${RIPPLE_MEDIA_BACKUP_DESTINATION}" in
  s3://*) ;;
  *) echo "RIPPLE_MEDIA_BACKUP_DESTINATION must use an s3:// URI." >&2; exit 1 ;;
esac

live_media_uri="s3://${MEDIA_S3_BUCKET}"
destination_bucket="${RIPPLE_MEDIA_BACKUP_DESTINATION#s3://}"
destination_bucket="${destination_bucket%%/*}"

if [[ "${destination_bucket}" == "${MEDIA_S3_BUCKET}" ]]; then
  echo "Independent media backup must use a different bucket from MEDIA_S3_BUCKET." >&2
  exit 1
fi

timestamp="${RIPPLE_BACKUP_TIMESTAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
release_sha="${RIPPLE_RELEASE_SHA:-unknown}"
mkdir -p "${RIPPLE_BACKUP_DIR}"
chmod 700 "${RIPPLE_BACKUP_DIR}"

plain_dump="${RIPPLE_BACKUP_DIR}/ripple-${timestamp}.dump"
encrypted_dump="${plain_dump}.enc"
manifest="${RIPPLE_BACKUP_DIR}/ripple-${timestamp}.sha256"

cleanup() {
  rm -f "${plain_dump}"
}
trap cleanup EXIT

echo "[1/5] Creating PostgreSQL logical backup..."
pg_dump --format=custom --no-owner --no-acl --file="${plain_dump}" "${DATABASE_URL}"

echo "[2/5] Verifying PostgreSQL backup catalog..."
pg_restore --list "${plain_dump}" >/dev/null

echo "[3/5] Encrypting logical backup..."
openssl enc -aes-256-cbc -pbkdf2 -salt   -pass env:RIPPLE_BACKUP_ENCRYPTION_PASSPHRASE   -in "${plain_dump}"   -out "${encrypted_dump}"
chmod 600 "${encrypted_dump}"

sha256sum "${encrypted_dump}" > "${manifest}"
chmod 600 "${manifest}"

echo "[4/5] Copying media to independent S3 destination without delete semantics..."
aws s3 sync "${live_media_uri}/" "${RIPPLE_MEDIA_BACKUP_DESTINATION%/}/"   --no-follow-symlinks   --only-show-errors

echo "[5/5] Backup set completed."
echo "Encrypted database backup: ${encrypted_dump}"
echo "Checksum manifest: ${manifest}"
echo "Media backup destination: ${RIPPLE_MEDIA_BACKUP_DESTINATION}"
echo "Release SHA: ${release_sha}"
echo "Timestamp (UTC): ${timestamp}"
echo
echo "Record these identifiers in the release/recovery log and verify destination-side encryption and retention."
