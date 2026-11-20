"""Contract tests for the one-command SMB pilot demo launcher."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "run-pilot-demo.sh").read_text()


def test_pilot_demo_launcher_builds_starts_and_waits_for_readiness():
    assert "docker compose" in SCRIPT
    assert "up -d --build" in SCRIPT
    assert "/health/ready" in SCRIPT
    assert "PILOT_DEMO_HEALTH_TIMEOUT" in SCRIPT


def test_pilot_demo_launcher_seeds_existing_idempotent_demo_content():
    assert "flask --app application seed-demo-content" in SCRIPT
    assert "/spaces/roadside-creators-club/operator" in SCRIPT
    assert "campfirecode@example.test" in SCRIPT
    assert "bytebloom@example.test" in SCRIPT


def test_pilot_demo_launcher_preserves_operator_authorization_boundary():
    assert "Expected anonymous operator route request to return 302" in SCRIPT
    assert 'if [[ "$status" != "302" ]]' in SCRIPT
    assert "curl" in SCRIPT


def test_pilot_demo_launcher_supports_lan_and_repeat_runs():
    assert 'RIPPLE_BIND_HOST="${RIPPLE_BIND_HOST:-0.0.0.0}"' in SCRIPT
    assert 'RIPPLE_PORT="${RIPPLE_PORT:-8000}"' in SCRIPT
    assert "PILOT_DEMO_SKIP_BUILD" in SCRIPT
    assert "docker compose down" in SCRIPT


def test_pilot_demo_launcher_does_not_destroy_data_or_provision_cloud_resources():
    assert "down -v" not in SCRIPT
    assert "terraform apply" not in SCRIPT
    assert "aws " not in SCRIPT


def test_pilot_demo_launcher_verifies_authenticated_owner_workflow():
    assert "Verifying authenticated owner workflow" in SCRIPT
    assert 'name="csrf_token"' in SCRIPT
    assert '--data-urlencode "email=campfirecode@example.test"' in SCRIPT
    assert '--data-urlencode "password=Passw0rd!"' in SCRIPT
    assert "Expected demo owner login to return 302" in SCRIPT
    assert "Expected authenticated operator dashboard to return 200" in SCRIPT
    assert "Community operating summary" in SCRIPT
    assert 'data-metric="member-count">8<' in SCRIPT
