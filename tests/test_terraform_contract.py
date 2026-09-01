from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
TERRAFORM = ROOT / "infra" / "terraform"


def read(name):
    return (TERRAFORM / name).read_text(encoding="utf-8")


def test_terraform_files_preserve_project_structure_contract():
    assert (TERRAFORM / "main.tf").exists()
    assert (TERRAFORM / "variables.tf").exists()
    assert (TERRAFORM / "outputs.tf").exists()
    assert (TERRAFORM / "versions.tf").exists()

    main = read("main.tf")
    variables = read("variables.tf")
    outputs = read("outputs.tf")

    assert 'variable "' not in main
    assert 'output "' not in main
    assert 'resource "' not in variables
    assert 'resource "' not in outputs


def test_terraform_toolchain_is_deliberately_pinned():
    versions = read("versions.tf")

    assert 'required_version = "< 1.17.0"' in versions
    assert 'source  = "hashicorp/aws"' in versions
    assert re.search(r'version\s*=\s*"\d+\.\d+\.\d+"', versions)


def test_terraform_matches_adr_0044_low_cost_topology():
    main = read("main.tf")
    variables = read("variables.tf")

    for required in (
        'resource "aws_vpc" "main"',
        'resource "aws_instance" "app"',
        'resource "aws_db_instance" "main"',
        'resource "aws_s3_bucket" "media"',
        'resource "aws_vpc_endpoint" "s3"',
        'resource "aws_iam_instance_profile" "app"',
        'resource "aws_eip" "app"',
        'publicly_accessible    = false',
        'http_tokens   = "required"',
        'block_public_policy     = true',
        'status = "Enabled"',
    ):
        assert required in main

    assert 'default     = "t4g.small"' in variables
    assert 'default     = "db.t4g.micro"' in variables
    assert 'default     = false' in variables
    assert 'enable_multi_az_rds' in variables


def test_terraform_does_not_add_disallowed_fixed_cost_launch_components():
    main = read("main.tf")

    for disallowed in (
        'resource "aws_nat_gateway"',
        'resource "aws_lb"',
        'resource "aws_cloudfront_distribution"',
        'resource "aws_elasticache',
        'resource "aws_ecs_',
        'resource "aws_eks_',
    ):
        assert disallowed not in main


def test_terraform_secret_and_state_guardrails_are_documented():
    variables = read("variables.tf")
    outputs = read("outputs.tf")
    gitignore = read(".gitignore")
    guide = read("README.md")

    assert 'variable "db_password"' in variables
    assert "sensitive   = true" in variables
    assert "db_password" not in outputs
    assert "SECRET_KEY" not in outputs
    assert "STRIPE" not in outputs

    for ignored in ("*.tfstate", "*.tfplan", "terraform.tfvars"):
        assert ignored in gitignore

    assert "Do not run `terraform apply` without explicit spend authorization." in guide
    assert "Terraform state/plan data can still contain sensitive values." in guide
    assert "prevent_destroy = true" in read("main.tf")
