"""Regression coverage for local Docker Compose network exposure."""

from pathlib import Path


def test_compose_web_port_defaults_to_all_host_interfaces():
    compose = Path("compose.yaml").read_text()
    assert '${RIPPLE_BIND_HOST:-0.0.0.0}:${RIPPLE_PORT:-8000}:8000' in compose
    assert 'gunicorn --bind 0.0.0.0:8000' in compose


def test_example_environment_documents_lan_bind_host():
    env_example = Path(".env.example").read_text()
    assert "RIPPLE_BIND_HOST=0.0.0.0" in env_example
    assert "RIPPLE_PORT=8000" in env_example
