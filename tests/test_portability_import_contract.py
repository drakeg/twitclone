"""Sprint 18 Story 18.5 import/provenance contract coverage."""

from twitclone.portability_import_contract import (
    IMPORT_COLLECTION_POLICIES,
    IMPORT_ENABLED,
    PROVENANCE_REQUIRED_FIELDS,
    assess_portable_import,
)


def _document(**overrides):
    payload = {
        "format": "ripple-portable-export",
        "version": 5,
        "exported_at": "2026-09-23T03:00:00Z",
        "scope": "test",
        "account": {},
        "posts": [],
        "quotes": [],
        "replies": [],
        "resources": [],
        "space_memberships": [],
        "private_messages": [],
        "subscriptions": [],
        "entitlements": [],
        "creator_support_transactions": {"status": "not_available"},
        "media_manifest": {"packaged_bytes": False, "assets": []},
    }
    payload.update(overrides)
    return payload


def test_import_contract_is_explicitly_non_mutating():
    assert IMPORT_ENABLED is False
    result = assess_portable_import(_document())
    assert result["compatible"] is True
    assert result["import_enabled"] is False


def test_import_contract_rejects_unknown_format_and_version():
    result = assess_portable_import(_document(format="other", version=99))
    assert result["compatible"] is False
    assert any("unsupported format" in item for item in result["errors"])
    assert any("unsupported source version" in item for item in result["errors"])


def test_import_contract_blocks_privilege_and_private_relationship_state():
    for collection in (
        "space_memberships",
        "private_messages",
        "subscriptions",
        "entitlements",
        "creator_support_transactions",
    ):
        assert IMPORT_COLLECTION_POLICIES[collection]["disposition"] == "prohibited"


def test_import_contract_requires_reference_resolution_for_quotes_and_replies():
    assert IMPORT_COLLECTION_POLICIES["quotes"]["disposition"] == "blocked_dependency"
    assert IMPORT_COLLECTION_POLICIES["replies"]["disposition"] == "blocked_dependency"


def test_import_contract_treats_media_as_reference_only():
    assert IMPORT_COLLECTION_POLICIES["media_manifest"]["disposition"] == "reference_only"
    result = assess_portable_import(_document())
    assert result["collections"]["media_manifest"]["present"] is True
    assert result["collections"]["media_manifest"]["disposition"] == "reference_only"


def test_import_contract_surfaces_unknown_fields_for_review():
    result = assess_portable_import(_document(future_collection=[]))
    assert result["compatible"] is True
    assert result["warnings"] == ["unknown collections/fields require review: future_collection"]


def test_provenance_contract_identifies_minimum_source_identity():
    assert PROVENANCE_REQUIRED_FIELDS == (
        "source_format",
        "source_version",
        "source_exported_at",
        "source_collection",
        "source_record_id",
    )


def test_no_portable_import_route_or_write_endpoint_is_registered(app):
    import_routes = [
        rule.rule
        for rule in app.url_map.iter_rules()
        if "import" in rule.rule.lower() or "import" in rule.endpoint.lower()
    ]
    assert import_routes == []



def test_import_contract_accepts_previous_v4_export_for_compatibility_review():
    result = assess_portable_import(_document(version=4))
    assert result["compatible"] is True
    assert result["import_enabled"] is False
