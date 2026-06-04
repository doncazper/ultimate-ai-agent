from ultimate_ai_agent.core.tools.runtime.contracts import ToolRuntimeManifest


def build_tool_runtime_manifest(baseline_version: str = "0.37.0") -> ToolRuntimeManifest:
    return ToolRuntimeManifest(baseline_version=baseline_version)
