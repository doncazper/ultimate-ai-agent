from ultimate_ai_agent.core.tools.runtime.contracts import ToolInvocationDecision, ToolInvocationRequest, ToolRuntimeManifest
from ultimate_ai_agent.core.tools.runtime.invocation import evaluate_tool_invocation
from ultimate_ai_agent.core.tools.runtime.manifests import build_tool_runtime_manifest


class ToolRuntimeAdapter:
    def __init__(self, manifest: ToolRuntimeManifest | None = None) -> None:
        self.manifest = manifest or build_tool_runtime_manifest()

    def invoke(self, request: ToolInvocationRequest, replay_keys_seen: list[str] | None = None) -> ToolInvocationDecision:
        return evaluate_tool_invocation(request, self.manifest.policy, replay_keys_seen=replay_keys_seen)
