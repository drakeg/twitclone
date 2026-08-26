from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_renderer_is_zero_spend_and_supports_shell_and_ssm():
    text = (ROOT / "scripts" / "render-production-env.sh").read_text()
    assert 'RIPPLE_CONFIG_SOURCE:-shell' in text
    assert 'get-parameters-by-path' in text
    assert '--with-decryption' in text
    assert 'terraform' not in text.lower()
    assert 'put-parameter' not in text


def test_runtime_renderer_requires_core_production_settings():
    text = (ROOT / "scripts" / "render-production-env.sh").read_text()
    for key in ("SECRET_KEY", "DATABASE_URL", "MEDIA_S3_BUCKET", "STRIPE_BILLING_ENABLED"):
        assert key in text
    assert 'if [[ "${STRIPE_BILLING_ENABLED}" == "true" ]]' in text
    assert 'validate_value STRIPE_SECRET_KEY' in text
    assert 'validate_value STRIPE_WEBHOOK_SECRET' in text


def test_runtime_renderer_writes_private_file_atomically():
    text = (ROOT / "scripts" / "render-production-env.sh").read_text()
    assert 'umask 077' in text
    assert 'mktemp' in text
    assert 'chmod 600' in text
    assert 'mv "${tmp}" "${OUTPUT_FILE}"' in text


def test_production_template_documents_local_and_future_aws_paths():
    text = (ROOT / "deploy" / "env.production.example").read_text()
    assert 'Zero-spend/local handoff' in text
    assert 'Future AWS handoff' in text
    assert 'RIPPLE_CONFIG_SOURCE=ssm' in text
    assert '/ripple/production' in text
    assert 'do not provision Parameter Store resources yet' in text


def test_production_compose_consumes_host_only_environment_file():
    text = (ROOT / "compose.production.yaml").read_text()
    assert '${RIPPLE_ENV_FILE:-.env.production}' in text
    assert 'SECRET_KEY=' not in text
    assert 'STRIPE_SECRET_KEY=' not in text
