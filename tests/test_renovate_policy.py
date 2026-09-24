"""Sprint 20 Renovate review-policy coverage."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "renovate.json").read_text(encoding="utf-8"))


def _rules():
    return CONFIG["packageRules"]


def test_renovate_never_auto_merges_dependency_updates():
    assert CONFIG.get("automerge") is False
    assert all(rule.get("automerge") is not True for rule in _rules())


def test_runtime_python_patch_updates_are_grouped_across_manifest_and_lock():
    matches = [
        rule
        for rule in _rules()
        if rule.get("groupName") == "python runtime patch updates"
    ]
    assert len(matches) == 1
    rule = matches[0]
    assert rule["matchManagers"] == ["pip_requirements"]
    assert set(rule["matchFileNames"]) == {"requirements.in", "requirements.txt"}
    assert rule["matchUpdateTypes"] == ["patch"]


def test_development_ci_and_terraform_patch_updates_have_surface_groups():
    expected = {
        "python development patch updates": "pip_requirements",
        "github actions patch updates": "github-actions",
        "terraform patch updates": "terraform",
    }
    for group_name, manager in expected.items():
        matches = [
            rule
            for rule in _rules()
            if rule.get("groupName") == group_name
        ]
        assert len(matches) == 1
        assert matches[0]["matchManagers"] == [manager]
        assert matches[0]["matchUpdateTypes"] == ["patch"]


def test_minor_and_major_updates_remain_ungrouped_for_focused_review():
    rules = [
        rule
        for rule in _rules()
        if rule.get("matchUpdateTypes") == ["minor", "major"]
    ]
    assert len(rules) == 1
    assert rules[0].get("groupName") is None
    assert rules[0]["automerge"] is False


def test_python_runtime_constraints_remain_in_place():
    py_rules = [
        rule
        for rule in _rules()
        if rule.get("allowedVersions") == "3.12"
        and "python" in rule.get("matchPackageNames", [])
    ]
    managers = {
        manager
        for rule in py_rules
        for manager in rule.get("matchManagers", [])
    }
    assert {"pyenv", "dockerfile"} <= managers
