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
    Artifact,
    CapabilityKind,
    CapabilityManifest,
    CapabilityPolicy,
    CapabilityRegistry,
    CapabilityRunContext,
    CoordinationMode,
    CoordinationRiskLevel,
    Coordinator,
    RiskLevel,
    SideEffectLevel,
    tool_capability,
    wrap_tool,
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

    async def manifest_echo(envelope, context) -> Artifact:
        return Artifact(
            producer_capability_id=context["capability_id"],
            kind="smoke.manifest_result",
            content={"summary": f"manifest:{envelope.objective.strip()}"},
            summary="Manifest/coordinator smoke capability completed.",
            confidence=1.0,
        )

    registry.register(
        CapabilityManifest(
            id="smoke:manifest_echo",
            version="1.0.0",
            kind=CapabilityKind.tool,
            name="Manifest Echo",
            description="Return a deterministic artifact through the manifest/coordinator capability lane.",
            tags=["smoke", "manifest", "read"],
            examples=["Use for local capability registry manifest/coordinator smoke testing."],
            anti_examples=["Do not use for external calls, shell commands, writes, or production authority."],
            input_schema={"type": "object", "properties": {"objective": {"type": "string"}}},
            output_schema={"type": "object", "properties": {"summary": {"type": "string"}}},
            input_modes=["text", "structured_ref"],
            output_modes=["artifact"],
            side_effects=SideEffectLevel.read,
            risk_level=CoordinationRiskLevel.low,
            auth_scopes=["smoke:read"],
            data_classes=["public"],
            allowed_coordination_modes=[CoordinationMode.direct_tool],
            concurrency_safe=True,
            safety={
                "allow_parallel": True,
                "require_single_writer": False,
                "approval_required": False,
                "max_risk_level": CoordinationRiskLevel.low,
                "max_side_effect_level": SideEffectLevel.read,
            },
            metadata={"owner": "dev-smoke", "runtime_authority": "in_process_only"},
        ),
        wrap_tool("smoke:manifest_echo", manifest_echo),
    )

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
    coordinator_result = Coordinator(registry).run(
        "local manifest registry ready",
        {
            "trace_id": "trace:capability-smoke-manifest",
            "auth_scopes": ["smoke:read"],
            "capability_ids": ["smoke:manifest_echo"],
        },
    )
    payload = {
        "ok": result.ok,
        "resolved_capability_names": [item.name for item in resolved],
        "openai_tool": capability_to_openai_tool(spec),
        "mcp_tool": capability_to_mcp_tool(spec),
        "manifest_coordinator_result": coordinator_result.model_dump(mode="json"),
        "result": result.model_dump(mode="json"),
        "no_backend_route_added": True,
        "no_provider_call_performed": True,
        "no_shell_or_network_authority": True,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
