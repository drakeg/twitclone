#!/usr/bin/env python3
"""Validate Mad Mallard repository standards for Ripple."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

REQUIRED_FILES = (
    "README.md",
    "AGENTS.md",
    "SPRINTS.md",
    "BACKLOG.md",
    "CONTRIBUTING.md",
    "RELEASES.md",
    "SECURITY.md",
)

START = "<!-- madmallard-badges:start -->"
END = "<!-- madmallard-badges:end -->"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8-sig")


def extract(pattern: str, text: str, label: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        fail(f"Unable to verify {label} from repository configuration")
    return match.group(1)


def expected_badge_tokens() -> tuple[str, ...]:
    python_version = read(".python-version").strip()
    requirements = read("requirements.in")
    flask_version = extract(r"^Flask==([^\s]+)$", requirements, "Flask version")
    terraform_ci = read(".github/workflows/ci.yml")
    terraform_version = extract(
        r'terraform_version:\s*"v?([^"]+)"',
        terraform_ci,
        "Terraform CI version",
    )
    terraform_versions = read("infra/terraform/versions.tf")
    aws_provider = extract(
        r'source\s*=\s*"hashicorp/aws"\s*\n\s*version\s*=\s*"([^"]+)"',
        terraform_versions,
        "AWS provider version",
    )
    variables = read("infra/terraform/variables.tf")
    postgres_version = extract(
        r'variable "postgres_engine_version"[\s\S]*?default\s*=\s*"([^"]+)"',
        variables,
        "PostgreSQL version",
    )

    return (
        f"Python-{python_version}-",
        f"Flask-{flask_version}-",
        f"PostgreSQL-{postgres_version}-",
        "Docker-supported-",
        "Docker_Compose-supported-",
        f"Terraform-{terraform_version}-",
        f"AWS_Provider-{aws_provider}-",
        "actions/workflows/ci.yml/badge.svg",
        "Security-policy-blue",
        "img.shields.io/github/issues/drakeg/twitclone",
        "img.shields.io/github/issues-pr/drakeg/twitclone",
    )


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        fail("Required repository standards files missing: " + ", ".join(missing))

    readme = README.read_text(encoding="utf-8-sig")
    if readme.count(START) != 1 or readme.count(END) != 1:
        fail("README must contain exactly one managed Mad Mallard badge block")

    first_h1_end = readme.find("\n")
    start_index = readme.find(START)
    if first_h1_end < 0 or not readme.startswith("# ") or start_index < first_h1_end:
        fail("Managed badge block must appear immediately below the first README H1")

    block = readme[start_index : readme.index(END) + len(END)]
    for token in expected_badge_tokens():
        if token not in block:
            fail(f"README badge block is missing or stale: {token}")

    # Repository currently has no published GitHub release and has no intentionally
    # selected license. These badges must remain absent until that state changes and
    # this validator is updated in the same reviewed PR.
    for unsupported in ("img.shields.io/github/v/release/", "img.shields.io/github/license/"):
        if unsupported in block:
            fail(f"README contains unsupported badge before repository state allows it: {unsupported}")

    backlog = read("BACKLOG.md")
    if "Resolve repository license intentionally" not in backlog:
        fail("BACKLOG.md must retain the explicit license-decision blocker")

    releases = read("RELEASES.md")
    if "No published GitHub release is currently available" not in releases:
        fail("RELEASES.md must accurately state the current no-release condition")

    print("OK: Mad Mallard repository standards and README badges are consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
