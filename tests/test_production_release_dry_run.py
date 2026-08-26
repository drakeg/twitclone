from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dry_run_is_zero_spend_and_non_mutating():
    script = (ROOT / "scripts" / "dry-run-production-release.sh").read_text()
    assert "deploy-production.sh\" validate" in script
    assert "terraform apply" not in script
    assert "docker compose up" not in script
    assert "compose pull" not in script
    assert "deployment-preflight" in script
    assert "no AWS resource was created" in script


def test_dry_run_requires_immutable_release_image():
    script = (ROOT / "scripts" / "dry-run-production-release.sh").read_text()
    assert "RIPPLE_IMAGE:?" in script
    assert '*":latest"' in script


def test_dry_run_uses_runtime_config_renderer():
    script = (ROOT / "scripts" / "dry-run-production-release.sh").read_text()
    assert "render-production-env.sh" in script
    assert "RIPPLE_CONFIG_SOURCE=env" in script
    assert "RIPPLE_ENV_FILE" in script


def test_dry_run_documents_release_and_rollback_sequence():
    script = (ROOT / "scripts" / "dry-run-production-release.sh").read_text()
    assert "pull image -> migrate -> deployment-preflight -> web/worker -> HTTPS proxy" in script
    assert "PREVIOUS_RIPPLE_IMAGE" in script
    assert "database migrations are never auto-downgraded" in script
