from typing import Any
import pytest

from ultimate_ai_agent.core.openwebui_bridge import (
    OpenWebUIBridgeManifest,
    OpenWebUIBridgePlan,
    OpenWebUIBridgeStatus,
    OpenWebUIChatSessionRef,
    build_default_openwebui_bridge_manifest,
)
from ultimate_ai_agent.core.openwebui_bridge.validation import (
    assert_agent_core_authority_boundary,
    assert_openwebui_contract_only,
    validate_openwebui_bridge_plan,
    validate_openwebui_chat_session_ref,
)


def test_manifest_rejects_openwebui_agent_brain_claim() -> None:
    manifest = OpenWebUIBridgeManifest(
        manifest_id="owui_manifest_authority",
        baseline_version="0.25.1",
        status=OpenWebUIBridgeStatus.contract_only,
        safe_summary="OpenWebUI contract manifest",
        openwebui_is_agent_brain=True,
    )

    with pytest.raises(ValueError, match="not the agent brain"):
        assert_agent_core_authority_boundary(manifest)


def test_manifest_rejects_missing_agent_core_authority() -> None:
    manifest = build_default_openwebui_bridge_manifest()
    manifest.agent_core_remains_authority = False

    with pytest.raises(ValueError, match="Agent Core remains authority"):
        assert_agent_core_authority_boundary(manifest)


def test_chat_session_refs_are_identifiers_not_authority() -> None:
    session = OpenWebUIChatSessionRef(
        session_ref="owui_session_demo",
        shell_ref="openwebui_local_shell_planned",
        user_ref="local_user_ref",
        safe_label="safe demo chat",
        authority_granted=True,
    )

    with pytest.raises(ValueError, match="session refs are not authority"):
        validate_openwebui_chat_session_ref(session)


def test_manifest_rejects_bridge_runtime_or_deployment_claims() -> None:
    manifest = build_default_openwebui_bridge_manifest()
    manifest.openwebui_integration_implemented = True
    manifest.deployment_config_added = True

    with pytest.raises(ValueError, match="integration is not implemented"):
        assert_openwebui_contract_only(manifest)


@pytest.mark.parametrize(
    "safe_warning",
    [
        "OpenWebUI is not the agent brain.",
        "OpenWebUI must not execute actions.",
        "OpenWebUI cannot approve actions.",
        "OpenWebUI does not bypass Python Agent Core authority.",
    ],
)
def test_negated_openwebui_authority_boundary_text_is_allowed(safe_warning: Any) -> None:
    plan = OpenWebUIBridgePlan(
        purpose="Keep the future shell contract-only.",
        allowed_scope=["redacted safe summaries only"],
        blocked_scope=["runtime execution"],
        warnings=[safe_warning],
    )

    assert validate_openwebui_bridge_plan(plan).warnings == [safe_warning]


@pytest.mark.parametrize(
    "authority_claim",
    [
        "OpenWebUI is the agent brain.",
        "OpenWebUI is the authority.",
        "OpenWebUI can execute actions.",
        "OpenWebUI can approve actions.",
        "OpenWebUI approves actions.",
    ],
)
def test_positive_openwebui_authority_claim_text_is_rejected(authority_claim: Any) -> None:
    plan = OpenWebUIBridgePlan(
        purpose="Keep the future shell contract-only.",
        allowed_scope=["redacted safe summaries only"],
        blocked_scope=["runtime execution"],
        warnings=[authority_claim],
    )

    with pytest.raises(ValueError, match="must not claim authority"):
        validate_openwebui_bridge_plan(plan)
