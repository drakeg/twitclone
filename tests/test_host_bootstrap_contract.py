from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "deploy" / "bootstrap-host.sh"
TERRAFORM = ROOT / "infra" / "terraform"


def test_bootstrap_is_amazon_linux_2023_container_host_only():
    script = BOOTSTRAP.read_text(encoding="utf-8")

    assert '[[ "${EUID}" -eq 0 ]]' in script
    assert '"${ID:-}" == "amzn"' in script
    assert '"${VERSION_ID:-}" == "2023"' in script
    assert "dnf install -y docker curl tar gzip" in script
    assert "systemctl enable --now docker" in script
    assert 'mkdir -p "${RIPPLE_ROOT}/deploy"' in script
    assert "docker compose version" in script


def test_bootstrap_requires_immutable_deployment_ref_and_pinned_compose():
    script = BOOTSTRAP.read_text(encoding="utf-8")

    assert "RIPPLE_DEPLOYMENT_REF" in script
    assert "40-character Git commit SHA" in script
    assert 'DOCKER_COMPOSE_VERSION="${DOCKER_COMPOSE_VERSION:-5.4.0}"' in script
    assert "fc5d1371f1ec7987e703da94ede49af3fbfb240b83f22991a98511de7bc4b93b" in script
    assert "sha256sum --check --status" in script
    assert '${RIPPLE_REPOSITORY_ARCHIVE_BASE}/${RIPPLE_DEPLOYMENT_REF}.tar.gz' in script


def test_bootstrap_installs_only_checked_in_deployment_contract():
    script = BOOTSTRAP.read_text(encoding="utf-8")

    for artifact in (
        "compose.production.yaml",
        "deploy/Caddyfile",
        "deploy/env.production.example",
        "scripts/deploy-production.sh",
    ):
        assert artifact in script

    assert "/etc/ripple/ripple.env" in script
    assert "No application secrets were created" in script
    assert "SECRET_KEY=" not in script
    assert "STRIPE_SECRET_KEY=" not in script
    assert "AWS_ACCESS_KEY_ID=" not in script


def test_terraform_ec2_user_data_uses_checked_in_bootstrap_without_secrets():
    main = (TERRAFORM / "main.tf").read_text(encoding="utf-8")
    variables = (TERRAFORM / "variables.tf").read_text(encoding="utf-8")
    template = (TERRAFORM / "templates" / "ec2-user-data.sh.tftpl").read_text(encoding="utf-8")

    assert 'variable "host_bootstrap_ref"' in variables
    assert 'regex("^[0-9a-fA-F]{40}$"' in variables
    assert 'templatefile(' in main
    assert 'base64encode(file("${path.module}/../../deploy/bootstrap-host.sh"))' in main
    assert "user_data_replace_on_change = true" in main
    assert "host_bootstrap_ref must be set" in main
    assert "bootstrap_script_b64" in template
    assert "deployment_ref" in template

    for secret in ("SECRET_KEY", "STRIPE_SECRET_KEY", "db_password", "DATABASE_URL"):
        assert secret not in template


def test_host_bootstrap_remains_no_spend_until_terraform_apply():
    script = BOOTSTRAP.read_text(encoding="utf-8")
    guide = (TERRAFORM / "README.md").read_text(encoding="utf-8")

    assert "terraform apply" not in script
    assert "aws ec2" not in script
    assert "aws rds" not in script
    assert "aws s3api create-bucket" not in script
    assert "Do not run `terraform apply` without explicit spend authorization." in guide
    assert "No AWS resource is required to review or test this contract." in guide
