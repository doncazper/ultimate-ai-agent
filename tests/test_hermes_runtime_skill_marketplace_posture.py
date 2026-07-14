import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_SKILL_MARKETPLACE_BLOCKED_AUTHORITY_REFS,
    RUNTIME_SKILL_MARKETPLACE_POSTURE_AUTHORITY_MAPPING_REF,
    RUNTIME_SKILL_MARKETPLACE_POSTURE_ROUTE_REF,
    RuntimeSkillMarketplaceCatalogSnapshot,
    RuntimeSkillMarketplacePostureReadModel,
    RuntimeSkillMarketplaceStage,
    build_runtime_skill_marketplace_posture_read_model,
)


client = TestClient(app)


def test_skill_marketplace_is_signal_review_adaptation_only() -> None:
    read_model = build_runtime_skill_marketplace_posture_read_model()

    assert read_model.schema_version == "runtime_skill_marketplace_posture.v1"
    assert read_model.status == "signal_review_adaptation_only"
    assert read_model.route_ref == RUNTIME_SKILL_MARKETPLACE_POSTURE_ROUTE_REF
    assert read_model.cli_ref == "uaa runtime inspect-skill-marketplace-posture"
    assert (
        read_model.authority_state_mapping_ref
        == RUNTIME_SKILL_MARKETPLACE_POSTURE_AUTHORITY_MAPPING_REF
    )
    assert read_model.authority_state_route_ref == "GET /api/runtime/authority-state"
    assert (
        read_model.authority_state_cli_ref
        == "repo-local-command:uaa-runtime-inspect-authority-state"
    )
    assert read_model.authority_state_decision_outcome == "allow"
    assert read_model.authority_state_status == "implemented_authority_bound_read_model"
    assert "reason-ref:authority:active-lease-grants-domain-capability" in (
        read_model.authority_state_reason_refs
    )
    assert "adapter-ref:skill-marketplace-external-code:not-implemented" in (
        read_model.unsupported_adapter_refs
    )
    assert read_model.stage_count == 7
    assert read_model.blocked_execution_count == 1
    assert read_model.external_popularity_is_trust is False
    assert read_model.external_code_execution_enabled is False
    assert read_model.direct_marketplace_install_enabled is False
    assert read_model.runtime_import_enabled is False
    assert read_model.automatic_skill_write_enabled is False
    assert read_model.provider_call_enabled is False
    assert read_model.browser_automation_enabled is False
    assert read_model.connector_write_enabled is False
    assert read_model.raw_marketplace_payload_persisted is False
    assert read_model.control_center_mints_authority is False
    assert read_model.catalog.entry_count == 31
    assert read_model.catalog.default_page_size == 25
    assert read_model.catalog.live_marketplace_fetch_performed is False
    assert read_model.catalog.raw_marketplace_payload_persisted is False
    assert set(RUNTIME_SKILL_MARKETPLACE_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


def test_skill_marketplace_route_returns_authority_bound_read_model() -> None:
    response = client.get("/api/runtime/skill-marketplace-posture")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_skill_marketplace_posture"
    data = body["data"]
    assert data["schema_version"] == "runtime_skill_marketplace_posture.v1"
    assert data["route_ref"] == "GET /api/runtime/skill-marketplace-posture"
    assert (
        data["authority_state_mapping_ref"]
        == "lane-ref:runtime-skill-marketplace-posture-read-model"
    )
    assert data["authority_state_decision_outcome"] == "allow"
    assert data["stage_count"] == 7
    assert data["blocked_execution_count"] == 1
    assert data["external_code_execution_enabled"] is False
    assert data["direct_marketplace_install_enabled"] is False
    assert data["runtime_import_enabled"] is False
    assert data["automatic_skill_write_enabled"] is False
    assert data["catalog"]["entry_count"] == 31
    assert data["catalog"]["pagination_supported"] is True


def test_skill_marketplace_catalog_keeps_source_signals_distinct() -> None:
    catalog = build_runtime_skill_marketplace_posture_read_model().catalog

    assert catalog.entry_count == 31
    assert {source.source_kind for source in catalog.sources} == {
        "clawhub",
        "hermes",
    }
    assert sum(entry.source_kind == "clawhub" for entry in catalog.entries) == 12
    assert sum(entry.source_kind == "hermes" for entry in catalog.entries) == 19
    clawhub = next(entry for entry in catalog.entries if entry.slug == "github")
    assert clawhub.rank_label == "#3 this week"
    assert clawhub.star_count == 651
    assert clawhub.download_count == 192948
    assert clawhub.average_rating is None
    assert clawhub.rating_count is None
    hermes = next(
        entry for entry in catalog.entries if entry.slug == "systematic-debugging"
    )
    assert hermes.rank_label == "Not provided by source"
    assert hermes.star_count is None
    assert hermes.download_count is None
    assert hermes.average_rating is None
    assert hermes.rating_count is None
    assert all(entry.risk_level == "unknown" for entry in catalog.entries)
    assert all(entry.review_required for entry in catalog.entries)
    assert all(not entry.external_code_imported for entry in catalog.entries)


def test_skill_marketplace_catalog_rejects_invented_hermes_signals() -> None:
    payload = (
        build_runtime_skill_marketplace_posture_read_model()
        .catalog.model_dump(mode="json")
    )
    hermes_entry = next(
        entry for entry in payload["entries"] if entry["source_kind"] == "hermes"
    )
    hermes_entry["star_count"] = 1

    with pytest.raises(
        ValueError,
        match="RUNTIME_SKILL_MARKETPLACE_HERMES_SIGNAL_NOT_PROVIDED",
    ):
        RuntimeSkillMarketplaceCatalogSnapshot(**payload)


def test_skill_marketplace_catalog_rejects_mismatched_source_identity() -> None:
    payload = (
        build_runtime_skill_marketplace_posture_read_model()
        .catalog.model_dump(mode="json")
    )
    hermes_entry = next(
        entry for entry in payload["entries"] if entry["source_kind"] == "hermes"
    )
    hermes_entry["source_kind"] = "clawhub"

    with pytest.raises(
        ValueError,
        match="RUNTIME_SKILL_MARKETPLACE_ENTRY_SOURCE_MISMATCH",
    ):
        RuntimeSkillMarketplaceCatalogSnapshot(**payload)


def test_skill_marketplace_catalog_rejects_duplicate_source_records() -> None:
    payload = (
        build_runtime_skill_marketplace_posture_read_model()
        .catalog.model_dump(mode="json")
    )
    payload["entries"][1]["source_record_ref"] = payload["entries"][0][
        "source_record_ref"
    ]

    with pytest.raises(
        ValueError,
        match="RUNTIME_SKILL_MARKETPLACE_SOURCE_RECORD_REFS_NOT_UNIQUE",
    ):
        RuntimeSkillMarketplaceCatalogSnapshot(**payload)


def test_skill_marketplace_catalog_rejects_future_dated_source_metadata() -> None:
    payload = (
        build_runtime_skill_marketplace_posture_read_model()
        .catalog.model_dump(mode="json")
    )
    payload["entries"][0]["source_updated_at"] = "2026-07-14T00:00:00Z"

    with pytest.raises(
        ValueError,
        match="RUNTIME_SKILL_MARKETPLACE_ENTRY_UPDATE_IN_FUTURE",
    ):
        RuntimeSkillMarketplaceCatalogSnapshot(**payload)


def test_skill_marketplace_snapshot_hash_binds_displayed_catalog_content() -> None:
    read_model = build_runtime_skill_marketplace_posture_read_model()
    payload = read_model.model_dump(mode="json")
    payload["catalog"]["entries"][0]["safe_summary"] = (
        "A different bounded summary that must invalidate the stored digest."
    )

    with pytest.raises(
        ValueError,
        match="RUNTIME_SKILL_MARKETPLACE_SNAPSHOT_HASH_MISMATCH",
    ):
        RuntimeSkillMarketplacePostureReadModel(**payload)


def test_skill_marketplace_stages_keep_external_signals_untrusted() -> None:
    read_model = build_runtime_skill_marketplace_posture_read_model()
    stage_kinds = {stage.stage_kind for stage in read_model.stages}

    assert stage_kinds == {
        "external_discovery_signal",
        "quarantine",
        "review",
        "adaptation_proposal",
        "uaa_owned_adaptation",
        "activation_grant",
        "execution_block",
    }
    for stage in read_model.stages:
        assert stage.stage_ref.startswith("skill-marketplace-stage-ref:")
        assert stage.signal_policy_ref.startswith("signal-policy-ref:")
        assert stage.quarantine_ref.startswith("quarantine-ref:")
        assert stage.review_ref.startswith("review-ref:")
        assert stage.adaptation_ref.startswith("adaptation-ref:")
        assert stage.activation_grant_ref.startswith("activation-grant-ref:")
        assert stage.external_popularity_is_trust is False
        assert stage.external_code_execution_enabled is False
        assert stage.direct_marketplace_install_enabled is False
        assert stage.runtime_import_enabled is False
        assert stage.automatic_skill_write_enabled is False
        assert stage.provider_call_enabled is False
        assert stage.browser_automation_enabled is False
        assert stage.connector_write_enabled is False
        assert stage.raw_marketplace_payload_persisted is False
        assert stage.control_center_mints_authority is False


@pytest.mark.parametrize(
    "field",
    [
        "external_popularity_is_trust",
        "external_code_execution_enabled",
        "direct_marketplace_install_enabled",
        "runtime_import_enabled",
        "automatic_skill_write_enabled",
        "provider_call_enabled",
        "browser_automation_enabled",
        "connector_write_enabled",
        "raw_marketplace_payload_persisted",
        "control_center_mints_authority",
    ],
)
def test_skill_marketplace_read_model_denies_authority_flags(field: str) -> None:
    payload = build_runtime_skill_marketplace_posture_read_model().model_dump(
        mode="json"
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_SKILL_MARKETPLACE_READ_MODEL_AUTHORITY_DENIED",
    ):
        RuntimeSkillMarketplacePostureReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "external_popularity_is_trust",
        "external_code_execution_enabled",
        "direct_marketplace_install_enabled",
        "runtime_import_enabled",
        "automatic_skill_write_enabled",
        "provider_call_enabled",
        "browser_automation_enabled",
        "connector_write_enabled",
        "raw_marketplace_payload_persisted",
        "control_center_mints_authority",
    ],
)
def test_skill_marketplace_stage_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_skill_marketplace_posture_read_model()
        .stages[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_SKILL_MARKETPLACE_STAGE_AUTHORITY_DENIED",
    ):
        RuntimeSkillMarketplaceStage(**payload)


def test_skill_marketplace_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-skill-marketplace-posture",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "raw_marketplace_value" not in result.stdout
    assert "external_code_value" not in result.stdout
    payload = json.loads(result.stdout)
    read_model = payload["runtime_skill_marketplace_posture"]
    assert payload["external_popularity_trusted"] is False
    assert payload["external_code_execution_performed"] is False
    assert payload["direct_marketplace_install_performed"] is False
    assert payload["automatic_skill_write_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/skill-marketplace-posture"
    assert (
        read_model["authority_state_mapping_ref"]
        == "lane-ref:runtime-skill-marketplace-posture-read-model"
    )
    assert read_model["authority_state_decision_outcome"] == "allow"
    assert read_model["stage_count"] == 7
    assert read_model["blocked_execution_count"] == 1
    assert read_model["catalog"]["entry_count"] == 31
    assert read_model["catalog"]["live_marketplace_fetch_performed"] is False
