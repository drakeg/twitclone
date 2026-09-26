"""Sprint 20 dependency inventory coverage."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "report_dependency_inventory.py"


def _module():
    spec = importlib.util.spec_from_file_location("report_dependency_inventory", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_inventory_covers_all_supported_dependency_surfaces():
    module = _module()
    inventory = module.build_inventory(ROOT)

    assert inventory["format"] == "ripple-dependency-inventory"
    assert inventory["version"] == 1
    assert inventory["network_accessed"] is False
    assert inventory["unrecognized"] == []
    assert inventory["counts"]["python"] > 0
    assert inventory["counts"]["docker"] >= 2
    assert inventory["counts"]["github_actions"] > 0
    assert inventory["counts"]["terraform"] >= 2


def test_inventory_distinguishes_direct_locked_and_development_python_dependencies():
    module = _module()
    inventory = module.build_inventory(ROOT)

    python_entries = [
        item for item in inventory["entries"] if item["surface"] == "python"
    ]
    classes = {item["classification"] for item in python_entries}

    assert {"direct", "locked", "development"} <= classes

    direct_flask = [
        item
        for item in python_entries
        if item["classification"] == "direct" and item["name"] == "flask"
    ]
    locked_flask = [
        item
        for item in python_entries
        if item["classification"] == "locked" and item["name"] == "flask"
    ]
    assert direct_flask[0]["version"] == "==3.1.3"
    assert locked_flask[0]["version"] == "==3.1.3"


def test_inventory_reports_release_container_images():
    module = _module()
    inventory = module.build_inventory(ROOT)

    docker = [item for item in inventory["entries"] if item["surface"] == "docker"]
    assert any(
        item["classification"] == "runtime_image"
        and item["name"] == "python"
        and item["version"] == "3.12-slim"
        for item in docker
    )
    assert any(
        item["classification"] == "compose_image"
        and item["name"] == "caddy"
        and item["version"] == "2.11.4-alpine"
        for item in docker
    )


def test_inventory_reports_ci_actions_and_terraform_constraints():
    module = _module()
    inventory = module.build_inventory(ROOT)

    actions = [
        item for item in inventory["entries"] if item["surface"] == "github_actions"
    ]
    terraform = [
        item for item in inventory["entries"] if item["surface"] == "terraform"
    ]

    assert any(
        item["name"] == "actions/checkout" and item["version"] == "v7"
        for item in actions
    )
    assert any(
        item["classification"] == "provider"
        and item["name"] == "hashicorp/aws"
        and item["version"] == "6.66.0"
        for item in terraform
    )
    assert any(
        item["classification"] == "terraform_cli"
        and item["name"] == "terraform"
        and item["version"] == "< 1.17.0"
        for item in terraform
    )


def test_inventory_is_local_only_and_makes_no_currency_claim():
    module = _module()
    rendered = module.render_text(module.build_inventory(ROOT))

    assert "local-only" in rendered
    assert "does not determine whether a dependency is current" in rendered


def test_unrecognized_requirement_is_reported_and_fails_closed(tmp_path):
    module = _module()

    for path in (
        "Dockerfile",
        "compose.production.yaml",
        ".github/workflows/ci.yml",
        "infra/terraform/versions.tf",
    ):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((ROOT / path).read_text(encoding="utf-8"), encoding="utf-8")

    (tmp_path / "requirements.in").write_text("Flask===3.1.3\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("Flask==3.1.3\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("-r requirements.txt\npytest>=9.1.1\n", encoding="utf-8")

    inventory = module.build_inventory(tmp_path)

    assert len(inventory["unrecognized"]) == 1
    assert inventory["unrecognized"][0]["source"] == "requirements.in"


def test_inventory_supports_bounded_development_requirements(tmp_path):
    module = _module()
    source = tmp_path / "requirements-dev.txt"
    source.write_text("pytest>=9.1.1,<9.2\n", encoding="utf-8")
    rows = module._requirements(source, "development", tmp_path)
    assert len(rows) == 1
    assert rows[0]["parse_status"] == "ok"
    assert rows[0]["name"] == "pytest"
    assert rows[0]["version"] == ">=9.1.1,<9.2"
