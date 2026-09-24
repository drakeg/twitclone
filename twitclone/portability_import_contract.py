"""Non-mutating portability import compatibility contract.

This module deliberately does not write imported data. It provides a stable,
testable description of which portable-export collections could be considered
for a future import and which require explicit review or remain prohibited.
"""

PORTABLE_FORMAT = "ripple-portable-export"
SUPPORTED_SOURCE_VERSIONS = {4, 5}
IMPORT_ENABLED = False

IMPORT_COLLECTION_POLICIES = {
    "account": {
        "disposition": "review_required",
        "notes": "Profile fields may be mapped later, but username/email identity must never be overwritten automatically.",
    },
    "social_graph": {
        "disposition": "reference_only",
        "notes": "External usernames may be resolved for preview only; imports must not silently create follows or followers.",
    },
    "posts": {
        "disposition": "candidate",
        "notes": "Authored post text may be eligible after duplicate handling, timestamp policy, and provenance persistence are implemented.",
    },
    "quotes": {
        "disposition": "blocked_dependency",
        "notes": "Quote import requires a resolvable local root-post mapping and must not copy another account's content.",
    },
    "replies": {
        "disposition": "blocked_dependency",
        "notes": "Reply import requires resolvable root/parent mappings and preserved authorship provenance.",
    },
    "resources": {
        "disposition": "candidate",
        "notes": "Owned resources and revisions may be eligible if revision order and original source identifiers are preserved.",
    },
    "space_memberships": {
        "disposition": "prohibited",
        "notes": "Portable data cannot grant space membership or roles; those remain controlled by the destination space.",
    },
    "private_messages": {
        "disposition": "prohibited",
        "notes": "Message import is not authorized because another participant's identity/content and deletion semantics are involved.",
    },
    "subscriptions": {
        "disposition": "prohibited",
        "notes": "Imported data cannot create or alter billing/subscription state.",
    },
    "entitlements": {
        "disposition": "prohibited",
        "notes": "Imported data cannot grant paid or administrative capabilities.",
    },
    "creator_support_transactions": {
        "disposition": "prohibited",
        "notes": "Ripple does not accept financial transaction claims from portable documents.",
    },
    "media_manifest": {
        "disposition": "reference_only",
        "notes": "References may be inventoried for preview only; Ripple must not fetch arbitrary paths or URLs during import assessment.",
    },
}

PROVENANCE_REQUIRED_FIELDS = (
    "source_format",
    "source_version",
    "source_exported_at",
    "source_collection",
    "source_record_id",
)


def assess_portable_import(document):
    """Return a non-mutating compatibility assessment for a portable document."""

    errors = []
    warnings = []

    if not isinstance(document, dict):
        return {
            "compatible": False,
            "import_enabled": IMPORT_ENABLED,
            "errors": ["document must be a JSON object"],
            "warnings": [],
            "collections": {},
        }

    source_format = document.get("format")
    source_version = document.get("version")

    if source_format != PORTABLE_FORMAT:
        errors.append(f"unsupported format: {source_format!r}")
    if source_version not in SUPPORTED_SOURCE_VERSIONS:
        errors.append(f"unsupported source version: {source_version!r}")

    if "exported_at" not in document:
        warnings.append("source exported_at is missing; provenance would be incomplete")

    collections = {}
    for name, policy in IMPORT_COLLECTION_POLICIES.items():
        present = name in document
        collections[name] = {
            "present": present,
            "disposition": policy["disposition"],
            "notes": policy["notes"],
        }

    unknown = sorted(
        key
        for key in document
        if key not in {
            "format",
            "version",
            "exported_at",
            "scope",
            "not_included",
            *IMPORT_COLLECTION_POLICIES.keys(),
        }
    )
    if unknown:
        warnings.append("unknown collections/fields require review: " + ", ".join(unknown))

    return {
        "compatible": not errors,
        "import_enabled": IMPORT_ENABLED,
        "errors": errors,
        "warnings": warnings,
        "collections": collections,
    }


__all__ = [
    "IMPORT_COLLECTION_POLICIES",
    "IMPORT_ENABLED",
    "PORTABLE_FORMAT",
    "PROVENANCE_REQUIRED_FIELDS",
    "SUPPORTED_SOURCE_VERSIONS",
    "assess_portable_import",
]
