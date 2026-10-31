import json
import re
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


def test_every_terraform_resource_is_classified_in_cost_inventory():
    main = (TERRAFORM / "main.tf").read_text(encoding="utf-8")
    inventory = json.loads((TERRAFORM / "cost-inventory.json").read_text(encoding="utf-8"))

    declared = {
        f"{resource_type}.{resource_name}"
        for resource_type, resource_name in RESOURCE_RE.findall(main)
    }
    classified = set(inventory["resources"])

    assert classified == declared


def test_cost_inventory_uses_explicit_supported_classes():
    inventory = json.loads((TERRAFORM / "cost-inventory.json").read_text(encoding="utf-8"))

    assert inventory["schema_version"] == 1
    assert inventory["reviewed_on"]
    assert inventory["region"] == "us-east-1"

    for address, metadata in inventory["resources"].items():
        assert metadata["cost_class"] in ALLOWED_COST_CLASSES, address
        assert metadata["component"].strip(), address

        if metadata["cost_class"].startswith("conditional_"):
            assert metadata.get("enabled_by"), address


def test_known_recurring_launch_components_cannot_be_reclassified_silently():
    inventory = json.loads((TERRAFORM / "cost-inventory.json").read_text(encoding="utf-8"))
    resources = inventory["resources"]

    assert resources["aws_instance.app"]["cost_class"] == "recurring"
    assert resources["aws_db_instance.main"]["cost_class"] == "recurring"
    assert resources["aws_eip.app"]["cost_class"] == "recurring"
    assert resources["aws_s3_bucket.media"]["cost_class"] == "usage_based"
    assert resources["aws_route53_zone.main"]["cost_class"] == "conditional_recurring"
    assert resources["aws_route53_zone.main"]["enabled_by"] == "enable_route53"
