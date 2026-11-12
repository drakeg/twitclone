#!/usr/bin/env bash
set -euo pipefail

: "${RIPPLE_ENCRYPTED_DB_BACKUP:?Set RIPPLE_ENCRYPTED_DB_BACKUP to the encrypted database backup artifact}"
: "${RIPPLE_DB_BACKUP_CHECKSUM_FILE:?Set RIPPLE_DB_BACKUP_CHECKSUM_FILE to its SHA-256 manifest}"
: "${RIPPLE_BACKUP_ENCRYPTION_PASSPHRASE:?Set RIPPLE_BACKUP_ENCRYPTION_PASSPHRASE from a secure runtime source}"
: "${RESTORE_DATABASE_URL:?Set RESTORE_DATABASE_URL to an isolated empty rehearsal database}"
: "${RIPPLE_RESTORE_MEDIA_DESTINATION:?Set RIPPLE_RESTORE_MEDIA_DESTINATION to an isolated s3:// bucket or prefix}"
: "${RIPPLE_MEDIA_BACKUP_SOURCE:?Set RIPPLE_MEDIA_BACKUP_SOURCE to the independent media backup s3:// URI}"

if [[ -n "${DATABASE_URL:-}" && "${RESTORE_DATABASE_URL}" == "${DATABASE_URL}" ]]; then
  echo "RESTORE_DATABASE_URL must not equal DATABASE_URL." >&2
  exit 1
fi

case "${RIPPLE_RESTORE_MEDIA_DESTINATION}" in
  s3://*) ;;
  *) echo "RIPPLE_RESTORE_MEDIA_DESTINATION must use an s3:// URI." >&2; exit 1 ;;
esac

case "${RIPPLE_MEDIA_BACKUP_SOURCE}" in
  s3://*) ;;
  *) echo "RIPPLE_MEDIA_BACKUP_SOURCE must use an s3:// URI." >&2; exit 1 ;;
esac

restore_bucket="${RIPPLE_RESTORE_MEDIA_DESTINATION#s3://}"
restore_bucket="${restore_bucket%%/*}"

if [[ -n "${MEDIA_S3_BUCKET:-}" && "${restore_bucket}" == "${MEDIA_S3_BUCKET}" ]]; then
  echo "Restore rehearsal media destination must not be the live MEDIA_S3_BUCKET." >&2
  exit 1
fi

for command in sha256sum openssl pg_restore aws; do
  command -v "${command}" >/dev/null 2>&1 || {
    echo "Required command not found: ${command}" >&2
    exit 1
  }
done

[[ -f "${RIPPLE_ENCRYPTED_DB_BACKUP}" ]] || {
  echo "Encrypted database backup not found: ${RIPPLE_ENCRYPTED_DB_BACKUP}" >&2
  exit 1
}
[[ -f "${RIPPLE_DB_BACKUP_CHECKSUM_FILE}" ]] || {
  echo "Checksum manifest not found: ${RIPPLE_DB_BACKUP_CHECKSUM_FILE}" >&2
  exit 1
}

work_dir="${RIPPLE_RESTORE_WORK_DIR:-$(mktemp -d)}"
mkdir -p "${work_dir}"
chmod 700 "${work_dir}"
plain_dump="${work_dir}/ripple-restore.dump"

cleanup() {
  rm -f "${plain_dump}"
  if [[ -z "${RIPPLE_RESTORE_WORK_DIR:-}" ]]; then
    rmdir "${work_dir}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

echo "[1/5] Verifying encrypted database backup checksum..."
(
  cd "$(dirname "${RIPPLE_ENCRYPTED_DB_BACKUP}")"
  sha256sum --check "$(realpath "${RIPPLE_DB_BACKUP_CHECKSUM_FILE}")"
)

echo "[2/5] Decrypting database backup into protected temporary storage..."
openssl enc -d -aes-256-cbc -pbkdf2   -pass env:RIPPLE_BACKUP_ENCRYPTION_PASSPHRASE   -in "${RIPPLE_ENCRYPTED_DB_BACKUP}"   -out "${plain_dump}"
chmod 600 "${plain_dump}"

echo "[3/5] Verifying decrypted PostgreSQL backup catalog..."
pg_restore --list "${plain_dump}" >/dev/null

echo "[4/5] Restoring database into isolated rehearsal target..."
pg_restore --clean --if-exists --no-owner --no-acl   --dbname="${RESTORE_DATABASE_URL}"   "${plain_dump}"

echo "[5/5] Restoring media into isolated rehearsal destination..."
aws s3 sync "${RIPPLE_MEDIA_BACKUP_SOURCE%/}/" "${RIPPLE_RESTORE_MEDIA_DESTINATION%/}/"   --no-follow-symlinks   --only-show-errors

echo
echo "RESTORE REHEARSAL DATA RESTORE COMPLETE"
echo "Database target: isolated RESTORE_DATABASE_URL"
echo "Media target: ${RIPPLE_RESTORE_MEDIA_DESTINATION}"
echo "Next: start the matching immutable application image against these restored targets and complete the validation checklist in docs/operations.md."
