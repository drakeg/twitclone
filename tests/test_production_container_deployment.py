from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_production_compose_preserves_release_process_boundaries():
    compose = read("compose.production.yaml")

    for service in ("migrate:", "preflight:", "web:", "worker:", "proxy:"):
        assert service in compose

    assert "flask --app application db upgrade" in compose
    assert "flask --app application deployment-preflight" in compose
    assert "python -m twitclone.scheduled_worker" in compose
    assert "gunicorn --bind 0.0.0.0:8000" in compose
    assert "condition: service_completed_successfully" in compose
    assert "condition: service_healthy" in compose


def test_production_compose_uses_release_image_and_does_not_build_source():
    compose = read("compose.production.yaml")

    assert "RIPPLE_IMAGE" in compose
    assert "build:" not in compose
    assert "8000:8000" not in compose
    assert "./deploy/Caddyfile:/etc/caddy/Caddyfile:ro" in compose


def test_production_environment_template_requires_postgres_and_private_media():
    environment = read("deploy/env.production.example")

    assert "TWITCLONE_ENV=production" in environment
    assert "DATABASE_URL=postgresql://" in environment
    assert "MEDIA_STORAGE_BACKEND=s3" in environment
    assert "MEDIA_S3_BUCKET=" in environment
    assert "MEDIA_S3_REGION=" in environment
    assert "AWS_ACCESS_KEY_ID" not in environment
    assert "AWS_SECRET_ACCESS_KEY" not in environment


def test_deployment_wrapper_is_container_only_and_rejects_latest():
    script = read("scripts/deploy-production.sh")

    assert '"${RIPPLE_IMAGE}" == *":latest"' in script
    assert "docker compose" in script
    assert "compose run --rm --no-deps migrate" in script
    assert "compose run --rm --no-deps preflight" in script
    assert "terraform apply" not in script.lower()
    assert "never runs Terraform" in script


def test_container_deployment_docs_preserve_zero_spend_local_workflow():
    guide = read("docs/container-deployment.md")

    assert "docker compose up --build" in guide
    assert "RIPPLE_PORT=8001 docker compose up --build" in guide
    assert "No AWS resources or recurring spend are required" in guide
    assert "does **not** run `terraform apply`" in guide
    assert "PREVIOUS_RIPPLE_IMAGE" in guide
    assert "IAM instance role" in guide
