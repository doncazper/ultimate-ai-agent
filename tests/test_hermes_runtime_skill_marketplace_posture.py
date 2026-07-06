import json
import subprocess
import sys

import pytest

from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_SKILL_MARKETPLACE_BLOCKED_AUTHORITY_REFS,
    RuntimeSkillMarketplacePostureReadModel,
    RuntimeSkillMarketplaceStage,
    build_runtime_skill_marketplace_posture_read_model,
)


def test_skill_marketplace_is_signal_review_adaptation_only() -> None:
    read_model = build_runtime_skill_marketplace_posture_read_model()

    assert read_model.schema_version == "runtime_skill_marketplace_posture.v1"
    assert read_model.status == "signal_review_adaptation_only"
    assert read_model.cli_ref == "uaa runtime inspect-skill-marketplace-posture"
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
    assert set(RUNTIME_SKILL_MARKETPLACE_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


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
    assert read_model["stage_count"] == 7
    assert read_model["blocked_execution_count"] == 1
