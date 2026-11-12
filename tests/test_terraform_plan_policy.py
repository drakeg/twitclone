import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-terraform-plan.py"


def run_validator(tmp_path, resource_changes, *extra):
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"resource_changes": resource_changes}), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(plan), *extra],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def change(address, actions=None):
    return {
        "address": address,
        "mode": "managed",
        "type": address.split(".", 1)[0],
        "change": {"actions": actions or ["create"]},
    }


def test_plan_validator_accepts_approved_default_topology(tmp_path):
    result = run_validator(
        tmp_path,
        [
            change("aws_instance.app"),
            change("aws_db_instance.main"),
            change("aws_s3_bucket.media"),
        ],
    )
    assert result.returncode == 0
    assert "does not authorize terraform apply or AWS spend" in result.stdout


def test_plan_validator_blocks_unknown_resource(tmp_path):
    result = run_validator(tmp_path, [change("aws_nat_gateway.main")])
    assert result.returncode == 1
    assert "outside the approved cost inventory" in result.stderr


def test_plan_validator_requires_explicit_conditional_cost_approval(tmp_path):
    result = run_validator(tmp_path, [change("aws_route53_zone.main")])
    assert result.returncode == 1
    assert "conditional-cost resources without explicit approval" in result.stderr


def test_plan_validator_accepts_explicit_conditional_resource(tmp_path):
    result = run_validator(
        tmp_path,
        [change("aws_route53_zone.main")],
        "--allow-conditional",
        "aws_route53_zone.main",
    )
    assert result.returncode == 0
    assert "Explicit conditional-cost approvals" in result.stdout


def test_plan_validator_rejects_stale_conditional_approval(tmp_path):
    result = run_validator(
        tmp_path,
        [change("aws_instance.app")],
        "--allow-conditional",
        "aws_route53_zone.main",
    )
    assert result.returncode == 1
    assert "not present in this plan" in result.stderr
