import pytest

from ultimate_ai_agent.core.openwebui_bridge import (
    OpenWebUIBridgeManifest,
    OpenWebUIBridgeStatus,
    OpenWebUIChatSessionRef,
    build_default_openwebui_bridge_manifest,
)
from ultimate_ai_agent.core.openwebui_bridge.validation import (
    assert_agent_core_authority_boundary,
    assert_openwebui_contract_only,
    validate_openwebui_chat_session_ref,
)


def test_manifest_rejects_openwebui_agent_brain_claim():
    manifest = OpenWebUIBridgeManifest(
        manifest_id="owui_manifest_authority",
        baseline_version="0.25.0",
        status=OpenWebUIBridgeStatus.contract_only,
        safe_summary="OpenWebUI contract manifest",
        openwebui_is_agent_brain=True,
    )

    with pytest.raises(ValueError, match="not the agent brain"):
        assert_agent_core_authority_boundary(manifest)


def test_manifest_rejects_missing_agent_core_authority():
    manifest = build_default_openwebui_bridge_manifest()
    manifest.agent_core_remains_authority = False

    with pytest.raises(ValueError, match="Agent Core remains authority"):
        assert_agent_core_authority_boundary(manifest)


def test_chat_session_refs_are_identifiers_not_authority():
    session = OpenWebUIChatSessionRef(
        session_ref="owui_session_demo",
        shell_ref="openwebui_local_shell_planned",
        user_ref="local_user_ref",
        safe_label="safe demo chat",
        authority_granted=True,
    )

    with pytest.raises(ValueError, match="session refs are not authority"):
        validate_openwebui_chat_session_ref(session)


def test_manifest_rejects_bridge_runtime_or_deployment_claims():
    manifest = build_default_openwebui_bridge_manifest()
    manifest.openwebui_integration_implemented = True
    manifest.deployment_config_added = True

    with pytest.raises(ValueError, match="integration is not implemented"):
        assert_openwebui_contract_only(manifest)
