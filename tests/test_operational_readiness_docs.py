from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_operations_runbook_defines_complete_recovery_boundary():
    runbook = read("docs/operations.md")

    for required in (
        "recovery point objective (RPO)",
        "recovery time objective (RTO)",
        "pg_dump --format=custom",
        "pg_restore --clean --if-exists",
        "independent backup",
        "object versioning",
        "migrate-media-to-s3 --source /path/to/uploads --dry-run",
        "SHA-256 content digest",
        "flask --app application deployment-preflight",
        "Deployment preflight passed.",
        "previous known-good SHA",
        "Public traffic is not approved",
    ):
        assert required in runbook


def test_cost_estimate_has_date_total_and_first_party_sources():
    estimate = read("docs/deployment-costs.md")

    assert "2026-08-23" in estimate
    assert "~31–35/month" in estimate
    assert "EC2 `t4g.small`" in estimate
    assert "RDS PostgreSQL 18 `db.t4g.micro`" in estimate
    assert "https://aws.amazon.com/ec2/pricing/on-demand/" in estimate
    assert "https://aws.amazon.com/vpc/pricing/" in estimate
    assert "https://aws.amazon.com/rds/postgresql/pricing/" in estimate
    assert "https://aws.amazon.com/s3/pricing/" in estimate
    assert "No paid infrastructure is authorized" in estimate


def test_local_compose_durable_state_contract_remains_intact():
    compose = read("compose.yaml")

    assert "DATABASE_URL: sqlite:////data/twitclone.db" in compose
    assert "UPLOAD_FOLDER: /data/uploads" in compose
    assert "twitclone_data:/data" in compose
    assert 'DATABASE_URL: "sqlite:///:memory:"' in compose


def test_administration_guide_documents_supported_promotion_command():
    guide = read("docs/administration.md")
    readme = read("README.md")

    command = "docker compose exec web flask --app application make-super-admin user@example.com"
    assert command in guide
    assert "flask --app application make-super-admin user@example.com" in guide
    assert "sets both the administrator and super-administrator flags" in guide
    assert "docs/administration.md" in readme


def test_release_readiness_template_covers_every_launch_gate():
    template = read("docs/templates/release-readiness-record.md")

    for required in (
        "Release SHA:",
        "Previous known-good SHA:",
        "Migration compatibility decision",
        "Database backup identifier:",
        "Media backup identifier:",
        "Rehearsal record location:",
        "Deployment preflight job identifier and result:",
        "Backup-failure alert owner:",
        "Result: approved / blocked / rolled back",
        "Do not commit completed records",
    ):
        assert required in template


def test_restore_rehearsal_template_records_objectives_and_cleanup():
    template = read("docs/templates/restore-rehearsal-record.md")

    for required in (
        "Source recovery-set identifier:",
        "No production database or live media bucket was targeted.",
        "flask --app application db current",
        "flask --app application deployment-preflight",
        "Observed RPO:",
        "Observed RTO:",
        "Exercise result: passed / failed",
        "Temporary resources were destroyed only after evidence was retained.",
    ):
        assert required in template
