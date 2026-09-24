"""Sprint 20 runtime-version alignment coverage."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_python_runtime_contract_is_consistent():
    supported = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    renovate = json.loads((ROOT / "renovate.json").read_text(encoding="utf-8"))
    verifier = (ROOT / "scripts" / "verify_dependencies.py").read_text(encoding="utf-8")

    assert supported == "3.12"
    assert re.search(r"^FROM python:3\.12-slim AS base$", dockerfile, re.MULTILINE)
    assert 'python-version: "3.12"' in ci
    assert "sys.version_info[:2] != (3, 12)" in verifier
    assert "Python 3.12.x is required" in verifier

    python_rules = [
        rule
        for rule in renovate["packageRules"]
        if "python" in rule.get("matchPackageNames", [])
    ]
    assert any(
        "pyenv" in rule.get("matchManagers", [])
        and rule.get("allowedVersions") == supported
        for rule in python_rules
    )
    assert any(
        "dockerfile" in rule.get("matchManagers", [])
        and rule.get("allowedVersions") == supported
        for rule in python_rules
    )


def test_release_image_does_not_use_newer_python_than_supported_runtime():
    supported = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    match = re.search(r"^FROM python:([0-9]+\.[0-9]+)-slim AS base$", dockerfile, re.MULTILINE)
    assert match is not None
    assert match.group(1) == supported
