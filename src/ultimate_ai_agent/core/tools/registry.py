from typing import Dict, List, Optional
from ultimate_ai_agent.core.tools.manifests import ToolManifest
from ultimate_ai_agent.core.tools.validation import validate_tool_manifest

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolManifest] = {}

    def register_tool(self, manifest: ToolManifest) -> None:
        validate_tool_manifest(manifest)
        self._tools[manifest.tool_id] = manifest

    def get_tool(self, tool_id: str) -> Optional[ToolManifest]:
        return self._tools.get(tool_id)

    def list_tools(self) -> List[ToolManifest]:
        return list(self._tools.values())
