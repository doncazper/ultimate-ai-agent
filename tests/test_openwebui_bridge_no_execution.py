import pytest

from ultimate_ai_agent.core.openwebui_bridge import (
    OpenWebUIBridgeManifest,
    OpenWebUIBridgeStatus,
    build_default_openwebui_bridge_manifest,
)
from ultimate_ai_agent.core.openwebui_bridge.validation import (
    assert_no_memory_write,
    assert_no_provider_call,
    assert_no_runtime_execution,
    assert_no_tool_execution,
)


@pytest.mark.parametrize(
    ("field", "helper", "message"),
    [
        ("tool_execution_enabled", assert_no_tool_execution, "tool execution"),
        ("memory_write_enabled", assert_no_memory_write, "memory write"),
        ("runtime_execution_enabled", assert_no_runtime_execution, "runtime execution"),
        ("provider_call_enabled", assert_no_provider_call, "provider call"),
    ],
)
def test_manifest_rejects_execution_capability_flags(field, helper, message):
    manifest = build_default_openwebui_bridge_manifest()
    setattr(manifest, field, True)

    with pytest.raises(ValueError, match=message):
        helper(manifest)


def test_openwebui_dependencies_or_config_are_not_required():
    manifest = OpenWebUIBridgeManifest(
        manifest_id="owui_manifest_no_deps",
        baseline_version="0.25.1",
        status=OpenWebUIBridgeStatus.contract_only,
        safe_summary="OpenWebUI bridge contract-only manifest",
    )

    assert manifest.dependencies_added is False
    assert manifest.openwebui_package_imported is False
    assert manifest.deployment_config_added is False
