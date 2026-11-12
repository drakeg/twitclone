from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "restore-rehearsal.sh").read_text(encoding="utf-8")


def test_restore_rehearsal_verifies_backup_before_restore():
    assert "sha256sum --check" in SCRIPT
    assert "openssl enc -d -aes-256-cbc -pbkdf2" in SCRIPT
    assert 'pg_restore --list "${plain_dump}"' in SCRIPT


def test_restore_rehearsal_uses_isolated_database_target():
    assert 'RESTORE_DATABASE_URL' in SCRIPT
    assert 'RESTORE_DATABASE_URL}" == "${DATABASE_URL}' in SCRIPT
    assert '--dbname="${RESTORE_DATABASE_URL}"' in SCRIPT
    assert "pg_restore --clean --if-exists --no-owner --no-acl" in SCRIPT


def test_restore_rehearsal_refuses_live_media_bucket():
    assert 'restore_bucket' in SCRIPT
    assert '== "${MEDIA_S3_BUCKET}"' in SCRIPT
    assert "must not be the live MEDIA_S3_BUCKET" in SCRIPT


def test_restore_rehearsal_never_uses_delete_or_creates_infrastructure():
    forbidden = (
        "--delete",
        "terraform apply",
        "aws s3 mb",
        "create-bucket",
        "create-db-instance",
    )
    for token in forbidden:
        assert token not in SCRIPT.lower()


def test_restore_rehearsal_cleans_plaintext_dump():
    assert 'rm -f "${plain_dump}"' in SCRIPT
