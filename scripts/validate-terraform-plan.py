#!/usr/bin/env python3
"""Validate a Terraform JSON plan against Ripple's approved topology/cost policy."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "infra" / "terraform" / "cost-inventory.json"
CONDITIONAL_CLASSES = {"conditional_recurring", "conditional_usage_based"}


def fail(message: str) -> None:
    print(f"BLOCKED: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate JSON emitted by 'terraform show -json' against Ripple's "
            "approved Terraform resource and cost inventory."
        )
    )
    parser.add_argument("plan_json", type=Path)
    parser.add_argument(
        "--allow-conditional",
        action="append",
        default=[],
        metavar="ADDRESS",
        help=(
            "Explicitly allow one conditional-cost Terraform resource address "
            "for this reviewed plan. Repeat for multiple resources."
        ),
    )
    return parser.parse_args()


def managed_resource_addresses(plan: dict) -> set[str]:
    addresses: set[str] = set()
    for change in plan.get("resource_changes", []):
        if change.get("mode", "managed") != "managed":
            continue
        address = change.get("address")
        if isinstance(address, str) and address:
            addresses.add(address)
    return addresses


def main() -> None:
    args = parse_args()

    try:
        plan = json.loads(args.plan_json.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"Plan JSON not found: {args.plan_json}")
    except json.JSONDecodeError as exc:
        fail(f"Invalid Terraform plan JSON: {exc}")

    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    resources = inventory.get("resources")
    if not isinstance(resources, dict):
        fail("cost-inventory.json must contain a resources object")

    planned = managed_resource_addresses(plan)
    approved = set(resources)
    unknown = sorted(planned - approved)
    if unknown:
        fail(
            "Plan contains managed resources outside the approved cost inventory: "
            + ", ".join(unknown)
        )

    allowed_conditional = set(args.allow_conditional)
    unknown_allowances = sorted(allowed_conditional - approved)
    if unknown_allowances:
        fail(
            "Conditional allowlist contains unknown resource addresses: "
            + ", ".join(unknown_allowances)
        )

    conditional_planned = sorted(
        address
        for address in planned
        if resources[address].get("cost_class") in CONDITIONAL_CLASSES
        and address not in allowed_conditional
    )
    if conditional_planned:
        fail(
            "Plan includes conditional-cost resources without explicit approval: "
            + ", ".join(conditional_planned)
        )

    stale_allowances = sorted(allowed_conditional - planned)
    if stale_allowances:
        fail(
            "Conditional allowlist includes resources not present in this plan: "
            + ", ".join(stale_allowances)
        )

    actions = {}
    for change in plan.get("resource_changes", []):
        if change.get("mode", "managed") != "managed":
            continue
        address = change.get("address")
        if address in planned:
            actions[address] = change.get("change", {}).get("actions", [])

    print(f"OK: validated {len(planned)} managed Terraform resource addresses.")
    if allowed_conditional:
        print(
            "Explicit conditional-cost approvals: "
            + ", ".join(sorted(allowed_conditional))
        )
    changed = sorted(
        address
        for address, resource_actions in actions.items()
        if resource_actions not in (["no-op"], [])
    )
    print(f"Resources with planned changes: {len(changed)}")
    print("This validation does not authorize terraform apply or AWS spend.")


if __name__ == "__main__":
    main()
