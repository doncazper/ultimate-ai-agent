from __future__ import annotations
from typing import Any

import json
import sys
from tempfile import TemporaryDirectory
from pathlib import Path

from pydantic import BaseModel, ConfigDict


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ultimate_ai_agent.core.capabilities import (  # noqa: E402
    Artifact,
    CapabilityApprovalGrant,
    CapabilityKind,
    CapabilityManifest,
    CapabilityPolicy,
    CapabilityRegistry,
    CapabilityRunContext,
    CoordinationMode,
    CoordinationRiskLevel,
    Coordinator,
    FileCoordinatorStateStore,
    LocalApprovalAuthority,
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

    async def manifest_echo(envelope: Any, context: Any) -> Artifact:
        return Artifact(
            producer_capability_id=context["capability_id"],
            kind="smoke.manifest_result",
            content={"summary": f"manifest:{envelope.objective.strip()}"},
            summary="Manifest/coordinator smoke capability completed.",
            confidence=1.0,
        )

    async def approved_review(envelope: Any, context: Any) -> Artifact:
        return Artifact(
            producer_capability_id=context["capability_id"],
            kind="smoke.approved_review",
            content={"summary": f"approved:{envelope.objective.strip()}"},
            summary="Approved manifest capability completed.",
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
    registry.register(
        CapabilityManifest(
            id="smoke:approved_review",
            version="1.0.0",
            kind=CapabilityKind.reviewer,
            name="Approved Review",
            description="Return a deterministic artifact only after exact local approval validation.",
            tags=["smoke", "approval", "read"],
            examples=["Use for local approved capability smoke testing."],
            anti_examples=["Do not use without an exact approval grant or for external side effects."],
            input_schema={"type": "object", "properties": {"objective": {"type": "string"}}},
            output_schema={"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]},
            input_modes=["text", "structured_ref"],
            output_modes=["artifact"],
            side_effects=SideEffectLevel.read,
            risk_level=CoordinationRiskLevel.high,
            approval_required="Smoke approval proves exact approval authority validation.",
            auth_scopes=["smoke:read"],
            data_classes=["public"],
            allowed_coordination_modes=[CoordinationMode.direct_tool],
            concurrency_safe=True,
            safety={
                "allow_parallel": True,
                "require_single_writer": False,
                "approval_required": True,
                "max_risk_level": CoordinationRiskLevel.high,
                "max_side_effect_level": SideEffectLevel.read,
            },
            metadata={"owner": "dev-smoke", "runtime_authority": "in_process_only"},
        ),
        wrap_tool("smoke:approved_review", approved_review),
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
    with TemporaryDirectory(prefix="uaa_capability_smoke_") as tmp_dir:
        state_path = Path(tmp_dir) / "coordinator_state.json"
        state_store = FileCoordinatorStateStore(state_path)
        approval_grant = CapabilityApprovalGrant(
            approval_ref="approval:capability-smoke-approved-review",
            capability_id="smoke:approved_review",
            granted_by="reviewer:dev-smoke",
            max_risk_level=CoordinationRiskLevel.high,
            max_side_effect_level=SideEffectLevel.read,
        )
        coordinator = Coordinator(
            registry,
            state_store=state_store,
            approval_authority=LocalApprovalAuthority(),
        )
        coordinator_result = coordinator.run(
            "local manifest registry ready",
            {
                "trace_id": "trace:capability-smoke-manifest",
                "auth_scopes": ["smoke:read"],
                "capability_ids": ["smoke:manifest_echo"],
            },
        )
        approved_result = coordinator.run(
            "local approved registry ready",
            {
                "trace_id": "trace:capability-smoke-approved",
                "auth_scopes": ["smoke:read"],
                "capability_ids": ["smoke:approved_review"],
                "approval_ref": approval_grant.approval_ref,
                "approval_grants": [approval_grant],
            },
        )
        reloaded_state = FileCoordinatorStateStore(state_path)
        state_summary = {
            "run_statuses": {
                trace_id: run.status
                for trace_id, run in sorted(reloaded_state.document.runs.items())
            },
            "audit_event_count": len(reloaded_state.document.audit_events),
            "telemetry_event_count": len(reloaded_state.document.telemetry_events),
        }
    payload = {
        "ok": result.ok,
        "resolved_capability_names": [item.name for item in resolved],
        "openai_tool": capability_to_openai_tool(spec),
        "mcp_tool": capability_to_mcp_tool(spec),
        "approved_manifest_result": approved_result.model_dump(mode="json"),
        "manifest_coordinator_result": coordinator_result.model_dump(mode="json"),
        "state_summary": state_summary,
        "result": result.model_dump(mode="json"),
        "no_backend_route_added": True,
        "no_provider_call_performed": True,
        "no_shell_or_network_authority": True,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
