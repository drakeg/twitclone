"""Verify that the declared dependency set is installed and importable.

This is intentionally lightweight and uses only the Python standard library so
it can run immediately after ``pip install -r requirements.txt``.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import sys
from pathlib import Path


REQUIRED_IMPORTS = {
    "apscheduler": "APScheduler",
    "bcrypt": "bcrypt",
    "flask": "Flask",
    "flask_bcrypt": "Flask-Bcrypt",
    "flask_login": "Flask-Login",
    "flask_migrate": "Flask-Migrate",
    "flask_sqlalchemy": "Flask-SQLAlchemy",
    "flask_wtf": "Flask-WTF",
    "PIL": "Pillow",
    "sqlalchemy": "SQLAlchemy",
    "wtforms": "WTForms",
}


def verify_python_version() -> list[str]:
    errors: list[str] = []
    if sys.version_info < (3, 12):
        errors.append(
            f"Python 3.12 or newer is required; found {sys.version.split()[0]}."
        )
    return errors


def verify_imports() -> list[str]:
    errors: list[str] = []
    for module_name, distribution_name in REQUIRED_IMPORTS.items():
        try:
            importlib.import_module(module_name)
            importlib.metadata.version(distribution_name)
        except (ImportError, importlib.metadata.PackageNotFoundError) as exc:
            errors.append(f"{distribution_name}: {exc}")
    return errors


def verify_requirements_file() -> list[str]:
    requirements = Path(__file__).resolve().parents[1] / "requirements.txt"
    if not requirements.is_file():
        return ["requirements.txt is missing."]
    if not requirements.read_text(encoding="utf-8").strip():
        return ["requirements.txt is empty."]
    return []


def main() -> int:
    errors = [
        *verify_python_version(),
        *verify_requirements_file(),
        *verify_imports(),
    ]

    if errors:
        print("Dependency verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Dependency verification passed on Python {sys.version.split()[0]}.")
    for _, distribution_name in REQUIRED_IMPORTS.items():
        print(f"- {distribution_name}=={importlib.metadata.version(distribution_name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
