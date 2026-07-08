import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
)
from ultimate_ai_agent.core.extension_catalog import (
    ExtensionInstallDisabledCandidateRecord,
    ExtensionInstallDisabledPostureReadModel,
    ExtensionInstallDisabledRecordReceipt,
    ExtensionInstallDisabledRecordStore,
    build_default_extension_install_disabled_posture,
    build_default_inspectable_extension_catalog,
    build_extension_install_disabled_approval_request,
    build_extension_install_disabled_record_receipt,
    validate_inspectable_extension_catalog,
)


client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]


def test_default_inspectable_extension_catalog_is_read_only_and_non_callable() -> None:
    catalog = build_default_inspectable_extension_catalog()
    payload = catalog.model_dump(mode="json")

    assert payload["schema_version"] == "uaa_inspectable_extension_catalog.v1"
    assert payload["catalog_status"] == "read_only_inspection"
    assert payload["read_only"] is True
    assert payload["inspectable_catalog_enabled"] is True
    assert payload["progressive_disclosure_enabled"] is True
    assert payload["metadata_first_index_enabled"] is True
    assert payload["callable_catalog_enabled"] is False
    assert payload["automatic_instruction_loading_enabled"] is False
    assert payload["full_instruction_auto_load_enabled"] is False
    assert payload["hidden_skill_activation_enabled"] is False
    assert payload["skill_runtime_import_enabled"] is False
    assert payload["external_marketplace_fetch_enabled"] is False
    assert payload["runtime_import_enabled"] is False
    assert payload["execution_enabled"] is False
    assert payload["connector_writes_enabled"] is False
    assert payload["shell_execution_enabled"] is False
    assert payload["network_access_enabled"] is False
    assert payload["browser_automation_enabled"] is False
    assert payload["mobile_control_enabled"] is False
    assert payload["public_distribution_claimed"] is False
    assert "plugin_runtime_import" in payload["blocked_capabilities"]
    assert "automatic_skill_instruction_loading" in payload["blocked_capabilities"]
    assert "hidden_skill_activation" in payload["blocked_capabilities"]
    assert "external_marketplace_fetch" in payload["blocked_capabilities"]
    assert "arbitrary_plugin_execution" in payload["blocked_capabilities"]
    assert "connector_writes" in payload["blocked_capabilities"]
    assert (
        "compact-skill-index:uaa-owned-progressive-disclosure"
        in payload["compact_skill_index_refs"]
    )
    assert (
        "progressive-disclosure:metadata-first-index"
        in payload["progressive_disclosure_refs"]
    )
    assert payload["skill_write_approval_gate"]["status"] == "staged_review_only"
    assert payload["skill_write_approval_gate"]["file_write_enabled"] is False
    assert payload["skill_bundle_proposal_posture"]["status"] == "proposal_only"
    assert payload["skill_bundle_proposal_posture"]["proposal_count"] == 1
    assert (
        payload["skill_bundle_proposal_posture"]["bundle_activation_enabled"] is False
    )
    assert payload["skill_bundle_proposal_posture"]["tool_execution_enabled"] is False
    install_posture = payload["install_disabled_posture"]
    assert install_posture["schema_version"] == "uaa_extension_install_disabled_posture.v1"
    assert install_posture["status"] == "blocked_pending_authority_and_approval"
    assert install_posture["install_disabled_posture_enabled"] is True
    assert install_posture["plugin_install_enabled"] is False
    assert install_posture["plugin_enablement_enabled"] is False
    assert install_posture["plugin_execution_enabled"] is False
    assert install_posture["runtime_import_enabled"] is False
    assert install_posture["side_effects_performed"] == []
    assert install_posture["candidate_count"] == 1
    install_candidate = install_posture["candidates"][0]
    assert install_candidate["authority_decision_outcome"] == "deny"
    assert install_candidate["exact_approval_required"] is True
    assert install_candidate["local_approval_validated"] is False
    assert install_candidate["approval_ref_authority"] is False
    assert install_candidate["disabled_install_record_ready"] is False
    assert install_candidate["disabled_install_record_persisted"] is False
    assert install_candidate["file_hashes"]
    assert all(
        item["hash_value"].startswith("sha256:")
        for item in install_candidate["file_hashes"]
        if item["hash_status"] == "reviewed"
    )
    assert "blocked-authority:extension-install-disabled:no-runtime-import" in (
        install_candidate["blocked_capability_refs"]
    )
    assert "doc:runtime-extensibility-final" in payload["docs_refs"]
    assert "doc:hermes-runtime-progressive-skill-disclosure" in payload["docs_refs"]
    assert "doc:hermes-runtime-skill-bundle-proposals" in payload["docs_refs"]
    assert (
        "doc:runtime-extensibility-final"
        in payload["developer_guidance_refs"]
    )
    assert (
        "verifier:runtime-extensibility-final"
        in payload["final_hardening_refs"]
    )

    reviewed_entry = payload["entries"][0]
    assert reviewed_entry["compact_skill_index_ref"].startswith("compact-skill-index:")
    assert reviewed_entry["metadata_summary_ref"].startswith("skill-metadata:")
    assert reviewed_entry["provenance"]["provenance_status"] == "reviewed"
    assert reviewed_entry["file_hashes"]
    assert all(
        item["file_ref"].startswith("file-ref:")
        for item in reviewed_entry["file_hashes"]
    )
    assert reviewed_entry["declared_capabilities"][0]["capability_ref"].startswith(
        "capability:"
    )
    assert reviewed_entry["activation_status"] == "future_scoped"
    assert reviewed_entry["visibility_status"] == "implemented"
    assert reviewed_entry["trust_posture"] == "reviewed_metadata"
    assert reviewed_entry["callable_posture"] == "inspectable_only"
    assert reviewed_entry["required_grant_refs"] == [
        "grant-request:extension-metadata-inspection"
    ]
    assert reviewed_entry["review_evidence_refs"]
    assert reviewed_entry["safe_adoption_posture"] == "repo_owned_metadata_only"
    assert reviewed_entry["progressive_disclosure_status"] == "metadata_indexed"
    assert (
        reviewed_entry["full_instruction_load_posture"]
        == "operator_selected_review_required"
    )
    assert reviewed_entry["metadata_first"] is True
    assert reviewed_entry["operator_selected_before_full_instruction"] is True
    assert reviewed_entry["automatic_instruction_loading_enabled"] is False
    assert reviewed_entry["hidden_activation_enabled"] is False
    assert "runtime import" in reviewed_entry["blocked_reason"]

    skill_entry = payload["entries"][1]
    assert skill_entry["package_identity"]["package_kind"] == "skill"
    assert skill_entry["progressive_disclosure_status"] == "metadata_indexed"
    assert skill_entry["callable_posture"] == "inspectable_only"
    assert skill_entry["trust_posture"] == "reviewed_metadata"
    assert skill_entry["metadata_first"] is True
    assert skill_entry["operator_selected_before_full_instruction"] is True
    assert skill_entry["automatic_instruction_loading_enabled"] is False
    assert skill_entry["hidden_activation_enabled"] is False
    assert "full instruction loading" in skill_entry["blocked_reason"]

    blocked_entry = payload["entries"][2]
    assert blocked_entry["provenance"]["provenance_status"] == "unknown"
    assert blocked_entry["blocked_state"] == "unknown"
    assert blocked_entry["activation_status"] == "blocked"
    assert blocked_entry["blocker_refs"]
    assert blocked_entry["visibility_status"] == "blocked"
    assert blocked_entry["trust_posture"] == "unknown_blocked"
    assert blocked_entry["callable_posture"] == "blocked_runtime"
    assert blocked_entry["required_grant_refs"] == ["grant-request:unknown-runtime"]
    assert blocked_entry["safe_adoption_posture"] == "blocked_until_scoped_milestone"
    assert blocked_entry["progressive_disclosure_status"] == "blocked"
    assert blocked_entry["full_instruction_load_posture"] == "blocked_runtime_import"


@pytest.mark.parametrize(
    "field",
    [
        "callable_catalog_enabled",
        "automatic_instruction_loading_enabled",
        "full_instruction_auto_load_enabled",
        "hidden_skill_activation_enabled",
        "skill_runtime_import_enabled",
        "external_marketplace_fetch_enabled",
        "runtime_import_enabled",
        "execution_enabled",
        "connector_writes_enabled",
        "shell_execution_enabled",
        "network_access_enabled",
        "browser_automation_enabled",
        "mobile_control_enabled",
        "public_distribution_claimed",
    ],
)
def test_inspectable_extension_catalog_validation_denies_runtime_authority(
    field: str,
) -> None:
    catalog = build_default_inspectable_extension_catalog().model_copy(
        update={field: True}
    )

    with pytest.raises(ValueError, match=f"EXTENSION_CATALOG_{field.upper()}_DENIED"):
        validate_inspectable_extension_catalog(catalog)


def test_extension_install_disabled_posture_requires_lease_and_exact_local_approval() -> None:
    approval_authority = LocalApprovalAuthority()
    approval_request = approval_authority.create_request(
        build_extension_install_disabled_approval_request()
    )
    grant = approval_authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="actor:operator",
        approval_ref="approval-ref:extension-install-disabled:test",
    )
    lease = AuthorityLease(
        lease_ref="authority-lease-ref:extension-install-disabled:test",
        mode=TrustMode.approved_safe_local_work_session,
        domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        safe_summary="Allow recording a disabled extension install ref for test.",
    )

    posture = build_default_extension_install_disabled_posture(
        leases=[lease],
        approval_authority=approval_authority,
        approval_ref=grant.approval_ref,
    )
    payload = posture.model_dump(mode="json")
    candidate = payload["candidates"][0]

    assert payload["status"] == "review_ready_disabled_not_persisted"
    assert candidate["authority_decision_outcome"] == "allow"
    assert candidate["approval_ref"] == grant.approval_ref
    assert candidate["local_approval_validated"] is True
    assert candidate["approval_validation_status"] == "approved"
    assert candidate["disabled_install_record_ready"] is True
    assert candidate["disabled_install_record_persisted"] is False
    assert candidate["plugin_install_enabled"] is False
    assert candidate["runtime_import_enabled"] is False
    assert candidate["plugin_execution_enabled"] is False

    receipt = build_extension_install_disabled_record_receipt(
        leases=[lease],
        approval_authority=approval_authority,
        approval_ref=grant.approval_ref,
    )
    receipt_payload = receipt.model_dump(mode="json")

    assert receipt_payload["schema_version"] == (
        "uaa_extension_install_disabled_record_receipt.v1"
    )
    assert receipt_payload["status"] == "disabled_install_record_receipt_recorded"
    assert receipt_payload["record_storage_mode"] == "receipt_only"
    assert receipt_payload["durable_store_persistence"] is False
    assert receipt_payload["authority_lease_ref"] == lease.lease_ref
    assert receipt_payload["authority_decision_outcome"] == "allow"
    assert receipt_payload["approval_ref"] == grant.approval_ref
    assert receipt_payload["local_approval_validated"] is True
    assert receipt_payload["approval_ref_authority"] is False
    assert receipt_payload["disabled_install_record_receipt_recorded"] is True
    assert receipt_payload["plugin_install_enabled"] is False
    assert receipt_payload["runtime_import_enabled"] is False
    assert receipt_payload["plugin_execution_enabled"] is False
    assert receipt_payload["side_effects_performed"] == []


def test_extension_install_disabled_record_receipt_denies_without_authority() -> None:
    with pytest.raises(
        ValueError,
        match="EXTENSION_INSTALL_DISABLED_RECORD_AUTHORITY_REQUIRED",
    ):
        build_extension_install_disabled_record_receipt()


def test_extension_install_disabled_record_store_is_idempotent(tmp_path: Path) -> None:
    approval_authority = LocalApprovalAuthority()
    approval_request = approval_authority.create_request(
        build_extension_install_disabled_approval_request()
    )
    grant = approval_authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="actor:operator",
        approval_ref="approval-ref:extension-install-disabled:store-test",
    )
    lease = AuthorityLease(
        lease_ref="authority-lease-ref:extension-install-disabled:store-test",
        mode=TrustMode.approved_safe_local_work_session,
        domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        safe_summary="Allow recording a disabled extension install ref for store test.",
    )
    receipt = build_extension_install_disabled_record_receipt(
        leases=[lease],
        approval_authority=approval_authority,
        approval_ref=grant.approval_ref,
    )

    store = ExtensionInstallDisabledRecordStore(tmp_path)
    persisted = store.record_receipt(receipt)
    replayed = store.record_receipt(receipt)
    records = list((tmp_path / "extension_install_disabled_records").glob("*.json"))

    assert persisted.receipt_ref == receipt.receipt_ref
    assert replayed.receipt_ref == persisted.receipt_ref
    assert persisted.durable_store_persistence is True
    assert persisted.record_storage_mode == "local_disabled_record_store"
    assert persisted.record_path_ref == (
        "storage-ref:extension-install-disabled-record:uaa-plugin-skill-boundary"
    )
    assert persisted.side_effects_performed == [
        "side-effect:extension-install-disabled:local-record-write"
    ]
    assert persisted.plugin_install_enabled is False
    assert persisted.runtime_import_enabled is False
    assert persisted.plugin_execution_enabled is False
    assert len(records) == 1

    changed_payload = ExtensionInstallDisabledRecordReceipt.model_validate(
        receipt.model_dump(mode="json")
        | {"approval_ref": "approval-ref:extension-install-disabled:changed-payload"}
    )
    with pytest.raises(
        ValueError,
        match="EXTENSION_INSTALL_DISABLED_IDEMPOTENCY_PAYLOAD_MISMATCH",
    ):
        store.record_receipt(changed_payload)


def test_extension_install_disabled_record_receipt_denies_runtime_flags() -> None:
    approval_authority = LocalApprovalAuthority()
    approval_request = approval_authority.create_request(
        build_extension_install_disabled_approval_request()
    )
    grant = approval_authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="actor:operator",
        approval_ref="approval-ref:extension-install-disabled:flag-test",
    )
    lease = AuthorityLease(
        lease_ref="authority-lease-ref:extension-install-disabled:flag-test",
        mode=TrustMode.approved_safe_local_work_session,
        domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        safe_summary="Allow recording a disabled extension install ref for flag test.",
    )
    receipt = build_extension_install_disabled_record_receipt(
        leases=[lease],
        approval_authority=approval_authority,
        approval_ref=grant.approval_ref,
    )

    with pytest.raises(ValueError, match="Input should be False"):
        ExtensionInstallDisabledRecordReceipt.model_validate(
            receipt.model_copy(update={"runtime_import_enabled": True}).model_dump()
        )


def test_extension_install_disabled_posture_denies_unsafe_mutation_flags() -> None:
    posture = build_default_extension_install_disabled_posture()

    with pytest.raises(ValueError, match="Input should be False"):
        ExtensionInstallDisabledPostureReadModel.model_validate(
            posture.model_copy(update={"plugin_install_enabled": True}).model_dump()
        )

    candidate = posture.candidates[0]
    with pytest.raises(ValueError, match="EXTENSION_INSTALL_DISABLED_READY_REQUIRES_AUTHORITY"):
        ExtensionInstallDisabledCandidateRecord.model_validate(
            candidate.model_copy(update={"disabled_install_record_ready": True}).model_dump()
        )


def test_extension_catalog_route_returns_safe_read_only_metadata() -> None:
    response = client.get("/extensions/catalog")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "inspect_extension_catalog"
    assert body["service"] == "ExtensionCatalogAPI"
    assert body["redactions_applied"] == [
        "safe_refs_only",
        "raw_package_content_omitted",
    ]

    catalog = body["data"]
    assert catalog["callable_catalog_enabled"] is False
    assert catalog["runtime_import_enabled"] is False
    assert catalog["execution_enabled"] is False
    assert catalog["install_disabled_posture"]["plugin_install_enabled"] is False
    assert (
        catalog["install_disabled_posture"]["candidates"][0]["authority_decision_outcome"]
        == "deny"
    )
    catalog_text = json.dumps(catalog).lower()
    assert "/users/" not in catalog_text
    assert "docs/" not in catalog_text
    assert "raw_prompt" not in catalog_text
    assert "raw_provider_payload" not in catalog_text


def test_extension_catalog_openapi_route_is_get_only_and_not_runtime_catalog() -> None:
    paths = app.openapi()["paths"]

    assert "/extensions/catalog" in paths
    assert sorted(paths["/extensions/catalog"].keys()) == ["get"]
    assert (
        paths["/extensions/catalog"]["get"]["operationId"] == "get_extensions_catalog"
    )
    for forbidden in [
        "/extensions/catalog/execute",
        "/extensions/catalog/import",
        "/extensions/catalog/activate",
        "/extensions/catalog/revoke",
        "/extensions/catalog/apply",
        "/extensions/catalog/install",
    ]:
        assert forbidden not in paths


def test_inspectable_extension_catalog_schema_pins_disabled_runtime_fields() -> None:
    schema = json.loads(
        (ROOT / "docs/schemas/inspectable_extension_catalog.schema.json").read_text(
            encoding="utf-8"
        )
    )

    assert schema["title"] == "uaa_inspectable_extension_catalog"
    assert schema["properties"]["catalog_status"]["const"] == "read_only_inspection"
    assert schema["properties"]["read_only"]["const"] is True
    assert schema["properties"]["progressive_disclosure_enabled"]["const"] is True
    assert schema["properties"]["metadata_first_index_enabled"]["const"] is True
    assert schema["properties"]["callable_catalog_enabled"]["const"] is False
    assert (
        schema["properties"]["automatic_instruction_loading_enabled"]["const"] is False
    )
    assert schema["properties"]["full_instruction_auto_load_enabled"]["const"] is False
    assert schema["properties"]["hidden_skill_activation_enabled"]["const"] is False
    assert schema["properties"]["skill_runtime_import_enabled"]["const"] is False
    assert schema["properties"]["external_marketplace_fetch_enabled"]["const"] is False
    assert schema["properties"]["runtime_import_enabled"]["const"] is False
    assert schema["properties"]["execution_enabled"]["const"] is False
    assert schema["properties"]["connector_writes_enabled"]["const"] is False
    entry = schema["$defs"]["catalog_entry"]
    for field in [
        "visibility_status",
        "trust_posture",
        "callable_posture",
        "compact_skill_index_ref",
        "metadata_summary_ref",
        "required_grant_refs",
        "blocked_reason",
        "review_evidence_refs",
        "safe_adoption_posture",
        "progressive_disclosure_status",
        "full_instruction_load_posture",
        "metadata_first",
        "operator_selected_before_full_instruction",
        "automatic_instruction_loading_enabled",
        "hidden_activation_enabled",
    ]:
        assert field in entry["required"]
        assert field in entry["properties"]
    assert "skill_write_approval_gate" in schema["required"]
    assert "skill_bundle_proposal_posture" in schema["required"]
    assert "install_disabled_posture" in schema["required"]
    gate = schema["$defs"]["skill_write_approval_gate"]
    assert gate["properties"]["status"]["const"] == "staged_review_only"
    assert gate["properties"]["file_write_enabled"]["const"] is False
    assert gate["properties"]["runtime_import_enabled"]["const"] is False
    posture = schema["$defs"]["skill_bundle_proposal_posture"]
    assert posture["properties"]["status"]["const"] == "proposal_only"
    assert posture["properties"]["bundle_activation_enabled"]["const"] is False
    assert posture["properties"]["tool_execution_enabled"]["const"] is False
    install_posture = schema["$defs"]["extension_install_disabled_posture"]
    assert install_posture["properties"]["install_disabled_posture_enabled"]["const"] is True
    assert install_posture["properties"]["plugin_install_enabled"]["const"] is False
    assert install_posture["properties"]["runtime_import_enabled"]["const"] is False
    install_candidate = schema["$defs"]["extension_install_disabled_candidate"]
    assert install_candidate["properties"]["exact_approval_required"]["const"] is True
    assert install_candidate["properties"]["approval_ref_authority"]["const"] is False
    assert install_candidate["properties"]["disabled_install_record_persisted"]["const"] is False
    assert install_candidate["properties"]["plugin_execution_enabled"]["const"] is False
