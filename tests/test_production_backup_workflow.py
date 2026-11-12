from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "backup-production.sh").read_text(encoding="utf-8")


def test_backup_workflow_creates_and_verifies_logical_dump():
    assert "pg_dump --format=custom --no-owner --no-acl" in SCRIPT
    assert 'pg_restore --list "${plain_dump}"' in SCRIPT


def test_backup_workflow_encrypts_database_dump_and_removes_plaintext():
    assert "openssl enc -aes-256-cbc -pbkdf2 -salt" in SCRIPT
    assert "RIPPLE_BACKUP_ENCRYPTION_PASSPHRASE" in SCRIPT
    assert 'rm -f "${plain_dump}"' in SCRIPT
    assert 'chmod 600 "${encrypted_dump}"' in SCRIPT
    assert "sha256sum" in SCRIPT


def test_media_backup_is_independent_and_never_uses_delete_semantics():
    assert 'aws s3 sync "${live_media_uri}/"' in SCRIPT
    assert 'destination_bucket' in SCRIPT
    assert '== "${MEDIA_S3_BUCKET}"' in SCRIPT
    assert "--delete" not in SCRIPT


def test_backup_workflow_requires_operator_supplied_destinations_and_secrets():
    for required in (
        "DATABASE_URL",
        "MEDIA_S3_BUCKET",
        "RIPPLE_BACKUP_DIR",
        "RIPPLE_BACKUP_ENCRYPTION_PASSPHRASE",
        "RIPPLE_MEDIA_BACKUP_DESTINATION",
    ):
        assert required in SCRIPT


def test_backup_workflow_does_not_create_infrastructure():
    forbidden = (
        "terraform apply",
        "aws s3 mb",
        "create-bucket",
        "create-db-instance",
    )
    for token in forbidden:
        assert token not in SCRIPT.lower()
