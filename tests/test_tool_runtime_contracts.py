import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.tools.runtime import (
    FILESYSTEM_METADATA_TOOL_REF,
    NOOP_TOOL_REF,
    ToolInvocationKind,
    ToolRuntimePolicy,
    build_tool_runtime_manifest,
)


def test_default_manifest_enables_allowlisted_safe_runtime():
    manifest = build_tool_runtime_manifest()

    assert manifest.policy.tool_runtime_enabled is True
    assert manifest.policy.noop_tool_enabled is True
    assert manifest.allowlisted_tool_refs == [NOOP_TOOL_REF, FILESYSTEM_METADATA_TOOL_REF]
    assert manifest.policy.arbitrary_tool_execution_enabled is False
    assert manifest.policy.side_effecting_tools_enabled is False
    assert manifest.policy.shell_tools_enabled is False
    assert manifest.policy.file_tools_enabled is False
    assert manifest.policy.memory_write_tools_enabled is False
    assert manifest.policy.network_tools_enabled is False
    assert manifest.policy.model_tools_enabled is False
    assert manifest.policy.browser_tools_enabled is False
    assert manifest.policy.mobile_tools_enabled is False
    assert manifest.policy.remote_tools_enabled is False
    assert manifest.policy.plugin_tools_enabled is False
    assert manifest.policy.dynamic_tool_registration_enabled is False


@pytest.mark.parametrize(
    "field_name",
    [
        "arbitrary_tool_execution_enabled",
        "side_effecting_tools_enabled",
        "shell_tools_enabled",
        "file_tools_enabled",
        "memory_write_tools_enabled",
        "network_tools_enabled",
        "model_tools_enabled",
        "browser_tools_enabled",
        "mobile_tools_enabled",
        "remote_tools_enabled",
        "plugin_tools_enabled",
        "dynamic_tool_registration_enabled",
    ],
)
def test_policy_rejects_runtime_expansion_flags(field_name):
    with pytest.raises(ValidationError):
        ToolRuntimePolicy(**{field_name: True})


def test_invocation_kind_exposes_noop_and_blocked_kinds():
    assert ToolInvocationKind.noop.value == "noop"
    assert ToolInvocationKind.blocked_file.value == "blocked_file"
    assert ToolInvocationKind.blocked_network.value == "blocked_network"
