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
        "previous known-good SHA",
        "Public traffic is not approved",
    ):
        assert required in runbook


def test_cost_estimate_has_date_total_and_first_party_sources():
    estimate = read("docs/deployment-costs.md")

    assert "2026-08-20" in estimate
    assert "$35.15–$40.15/month" in estimate
    assert "https://docs.digitalocean.com/products/app-platform/details/pricing/" in estimate
    assert "https://www.digitalocean.com/pricing/managed-databases" in estimate
    assert "https://docs.digitalocean.com/products/spaces/details/pricing/" in estimate


def test_local_compose_durable_state_contract_remains_intact():
    compose = read("compose.yaml")

    assert "DATABASE_URL: sqlite:////data/twitclone.db" in compose
    assert "UPLOAD_FOLDER: /data/uploads" in compose
    assert "twitclone_data:/data" in compose
    assert 'DATABASE_URL: "sqlite:///:memory:"' in compose
