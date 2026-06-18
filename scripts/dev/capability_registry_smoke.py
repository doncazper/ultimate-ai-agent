from __future__ import annotations

import json
import sys
from pathlib import Path

from pydantic import BaseModel, ConfigDict


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ultimate_ai_agent.core.capabilities import (  # noqa: E402
    CapabilityPolicy,
    CapabilityRegistry,
    CapabilityRunContext,
    RiskLevel,
    tool_capability,
)
from ultimate_ai_agent.core.capabilities.adapters import capability_to_mcp_tool, capability_to_openai_tool  # noqa: E402


class EchoInput(BaseModel):
    message: str

    model_config = ConfigDict(extra="forbid")


class EchoOutput(BaseModel):
    summary: str

    model_config = ConfigDict(extra="forbid")


def build_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()

    @tool_capability(
        name="smoke.echo_summary",
        title="Echo Summary",
        description="Return a deterministic local summary for capability registry smoke testing.",
        input_model=EchoInput,
        output_model=EchoOutput,
        tags={"smoke", "read"},
        policy=CapabilityPolicy(
            allowed_agents={"smoke.agent"},
            required_scopes={"smoke:read"},
            risk=RiskLevel.READ_ONLY,
            timeout_s=2.0,
            max_retries=0,
            idempotent=True,
        ),
        source="python",
        metadata={"owner": "dev-smoke", "side_effects": []},
        registry=registry,
    )
    async def echo_summary(ctx: CapabilityRunContext, args: EchoInput) -> EchoOutput:
        del ctx
        return EchoOutput(summary=f"smoke:{args.message.strip()}")

    return registry


def main() -> int:
    registry = build_registry()
    context = CapabilityRunContext(agent_name="smoke.agent", user_scopes={"smoke:read"}, trace_id="trace:capability-smoke")
    resolved = registry.resolve_for_run(context, query="echo summary", tags={"smoke"}, max_tools=5)
    if not resolved:
        print(json.dumps({"ok": False, "error": "NO_CAPABILITY_RESOLVED"}, sort_keys=True))
        return 1

    spec = resolved[0]
    result = registry.execute_sync(spec.name, {"message": "local registry ready"}, context)
    payload = {
        "ok": result.ok,
        "resolved_capability_names": [item.name for item in resolved],
        "openai_tool": capability_to_openai_tool(spec),
        "mcp_tool": capability_to_mcp_tool(spec),
        "result": result.model_dump(mode="json"),
        "no_backend_route_added": True,
        "no_provider_call_performed": True,
        "no_shell_or_network_authority": True,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
