from __future__ import annotations

import re

from ultimate_ai_agent.core.control_center.agent_loop import (
    build_external_information_handling_posture,
)
from ultimate_ai_agent.core.secrets import BlockedCredentialVaultAdapter
from ultimate_ai_agent.core.secrets.vault_readiness import (
    build_provider_credential_vault_adapter_readiness,
)


def test_external_intake_summary_is_renderable_without_relaxing_content_guard() -> None:
    posture = build_external_information_handling_posture()
    intake = next(
        row for row in posture["rows"]
        if row["category_id"] == "operator_supplied_external_metadata"
    )
    assert "without retaining source bodies" in intake["safe_summary"]
    assert not re.search(
        r"raw[_ -]?(?:prompt|response|page|payload|log)", intake["safe_summary"], re.I
    )
    assert intake["raw_content_included"] is False
    assert intake["external_content_can_grant_authority"] is False


def test_built_vault_readiness_preserves_dashboard_blocked_reason() -> None:
    report = BlockedCredentialVaultAdapter().inspect_capabilities()
    original_codes = list(report.blocker_codes)
    readiness = build_provider_credential_vault_adapter_readiness(report)

    assert "VAULT_ADAPTER_NOT_SCOPED" in readiness.blocker_codes
    assert set(original_codes).issubset(readiness.blocker_codes)
    assert report.blocker_codes == original_codes
    assert readiness.adapter_available is False
    assert readiness.adapter_runtime_enabled is False
    assert readiness.raw_key_visible is False
    assert readiness.credential_material_stored_by_repo is False
    assert readiness.readiness_status == "blocked_no_approved_backend"

    report_with_reason = report.model_copy(
        update={"blocker_codes": [*original_codes, "VAULT_ADAPTER_NOT_SCOPED"]}
    )
    assert build_provider_credential_vault_adapter_readiness(
        report_with_reason
    ).blocker_codes.count("VAULT_ADAPTER_NOT_SCOPED") == 1
