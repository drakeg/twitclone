"""Sprint 20 direct-dependency manifest and lock coverage."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "verify_dependency_lock.py"


def _module():
    spec = importlib.util.spec_from_file_location("verify_dependency_lock", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_current_direct_dependency_manifest_matches_lock():
    module = _module()
    assert module.verify_dependency_lock() == []


def test_direct_dependency_missing_from_lock_is_reported(tmp_path):
    module = _module()
    direct = tmp_path / "requirements.in"
    lock = tmp_path / "requirements.txt"
    direct.write_text("Flask==3.1.3\nboto3==1.43.101\n", encoding="utf-8")
    lock.write_text("Flask==3.1.3\n", encoding="utf-8")

    module.DIRECT = direct
    module.LOCK = lock

    assert module.verify_dependency_lock() == ["boto3: missing from requirements.txt"]


def test_direct_dependency_version_drift_is_reported(tmp_path):
    module = _module()
    direct = tmp_path / "requirements.in"
    lock = tmp_path / "requirements.txt"
    direct.write_text("Flask==3.1.3\n", encoding="utf-8")
    lock.write_text("Flask==3.2.0\n", encoding="utf-8")

    module.DIRECT = direct
    module.LOCK = lock

    errors = module.verify_dependency_lock()
    assert len(errors) == 1
    assert "requirements.in ==3.1.3" in errors[0]
    assert "requirements.txt ==3.2.0" in errors[0]


def test_manifest_parser_normalizes_names_and_accepts_extras(tmp_path):
    module = _module()
    direct = tmp_path / "requirements.in"
    lock = tmp_path / "requirements.txt"
    direct.write_text("psycopg[binary]==3.3.6\nFlask-Bcrypt==1.0.1\n", encoding="utf-8")
    lock.write_text("psycopg[binary]==3.3.6\nflask_bcrypt==1.0.1\n", encoding="utf-8")

    module.DIRECT = direct
    module.LOCK = lock

    assert module.verify_dependency_lock() == []


def test_unsupported_requirement_syntax_fails_closed(tmp_path):
    module = _module()
    direct = tmp_path / "requirements.in"
    lock = tmp_path / "requirements.txt"
    direct.write_text("Flask~=3.1\n", encoding="utf-8")
    lock.write_text("Flask==3.1.3\n", encoding="utf-8")

    module.DIRECT = direct
    module.LOCK = lock

    errors = module.verify_dependency_lock()
    assert len(errors) == 1
    assert "unsupported requirement syntax" in errors[0]


def test_triple_equals_requirement_fails_closed(tmp_path):
    module = _module()
    direct = tmp_path / "requirements.in"
    lock = tmp_path / "requirements.txt"
    direct.write_text("Flask===3.1.3\\n", encoding="utf-8")
    lock.write_text("Flask==3.1.3\\n", encoding="utf-8")
    module.DIRECT = direct
    module.LOCK = lock
    errors = module.verify_dependency_lock()
    assert len(errors) == 1
    assert "unsupported requirement syntax" in errors[0]
