from ultimate_ai_agent.core.tools.runtime.contracts import ToolInvocationDecision, ToolInvocationRequest, ToolRuntimeManifest
from ultimate_ai_agent.core.tools.runtime.filesystem_metadata import FilesystemSafeRoot
from ultimate_ai_agent.core.tools.runtime.http_fetch import HttpFetchTransport
from ultimate_ai_agent.core.tools.runtime.invocation import evaluate_tool_invocation
from ultimate_ai_agent.core.tools.runtime.manifests import build_tool_runtime_manifest


class ToolRuntimeAdapter:
    def __init__(self, manifest: ToolRuntimeManifest | None = None) -> None:
        self.manifest = manifest or build_tool_runtime_manifest()

    def invoke(
        self,
        request: ToolInvocationRequest,
        replay_keys_seen: list[str] | None = None,
        safe_roots: list[FilesystemSafeRoot] | None = None,
        http_fetch_transport: HttpFetchTransport | None = None,
    ) -> ToolInvocationDecision:
        return evaluate_tool_invocation(
            request,
            self.manifest.policy,
            replay_keys_seen=replay_keys_seen,
            safe_roots=safe_roots,
            http_fetch_transport=http_fetch_transport,
        )
