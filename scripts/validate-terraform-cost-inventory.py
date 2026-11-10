#!/usr/bin/env python3
"""Validate Terraform resource coverage in the cost inventory."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TERRAFORM = ROOT / "infra" / "terraform"
RESOURCE_RE = re.compile(r'^resource\s+"([^"]+)"\s+"([^"]+)"\s*{', re.MULTILINE)
ALLOWED_COST_CLASSES = {
    "no_direct_charge",
    "usage_based",
    "recurring",
    "conditional_recurring",
    "conditional_usage_based",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    main_tf = (TERRAFORM / "main.tf").read_text(encoding="utf-8")
    inventory_path = TERRAFORM / "cost-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))

    declared = {
        f"{resource_type}.{resource_name}"
        for resource_type, resource_name in RESOURCE_RE.findall(main_tf)
    }
    resources = inventory.get("resources")
    if not isinstance(resources, dict):
        fail("cost-inventory.json must contain a resources object")

    classified = set(resources)
    missing = sorted(declared - classified)
    stale = sorted(classified - declared)
    if missing:
        fail("Terraform resources missing from cost inventory: " + ", ".join(missing))
    if stale:
        fail("Cost inventory entries without Terraform resources: " + ", ".join(stale))

    for address, metadata in resources.items():
        if not isinstance(metadata, dict):
            fail(f"{address} metadata must be an object")
        cost_class = metadata.get("cost_class")
        if cost_class not in ALLOWED_COST_CLASSES:
            fail(f"{address} has unsupported cost_class: {cost_class!r}")
        if not str(metadata.get("component", "")).strip():
            fail(f"{address} must have a non-empty component description")
        if cost_class.startswith("conditional_") and not metadata.get("enabled_by"):
            fail(f"{address} must identify the variable that enables the conditional cost")

    print(
        f"OK: classified {len(declared)} Terraform resources in "
        f"{inventory_path.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
