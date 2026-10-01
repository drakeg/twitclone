from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = spec_from_file_location("validate_accessibility_evidence", ROOT / "scripts" / "validate-accessibility-evidence.py")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _record():
    return json.loads((ROOT / "docs" / "templates" / "accessibility-evidence.example.json").read_text(encoding="utf-8"))


def test_example_record_is_structurally_valid_but_blocked():
    module = _module()
    record = _record()
    assert record["review_decision"] == "blocked"
    assert module.validate_record(record) == []


def test_approved_record_requires_real_versions_and_all_passes():
    module = _module()
    record = _record()
    record["review_decision"] = "approved"
    errors = module.validate_record(record)
    assert any("template placeholder" in error for error in errors)
    assert any("assistive_technology_version" in error for error in errors)


def test_missing_required_scenario_fails_closed():
    module = _module()
    record = _record()
    record["scenarios"] = record["scenarios"][:-1]
    errors = module.validate_record(record)
    assert any("zoom-400-core-flows" in error for error in errors)


def test_failed_scenario_requires_defect_reference():
    module = _module()
    record = _record()
    record["scenarios"][0]["result"] = "fail"
    errors = module.validate_record(record)
    assert any("defect_reference is required" in error for error in errors)


def test_approved_complete_record_can_validate_without_authorizing_launch(tmp_path, capsys):
    module = _module()
    record = _record()
    record["review_decision"] = "approved"
    for scenario in record["scenarios"]:
        scenario["browser_version"] = "test-version"
        scenario["viewport"] = "1280x720"
        if scenario["platform"].startswith("replace-with-"):
            scenario["platform"] = "Windows"
        if scenario["browser"].startswith("replace-with-"):
            scenario["browser"] = "Chrome"
        if scenario["assistive_technology"] != "none":
            scenario["assistive_technology_version"] = "test-version"
        scenario["result"] = "pass"
    assert module.validate_record(record) == []

    path = tmp_path / "record.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    loaded, errors = module.validate_path(path)
    assert errors == []
    assert loaded["review_decision"] == "approved"


def test_release_sha_and_review_date_are_validated():
    module = _module()
    record = _record()
    record["release_sha"] = "not-a-sha"
    record["review_date"] = "09/30/2026"
    errors = module.validate_record(record)
    assert any("40-character" in error for error in errors)
    assert any("YYYY-MM-DD" in error for error in errors)
