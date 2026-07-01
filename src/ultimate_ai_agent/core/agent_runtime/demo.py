from __future__ import annotations

from ultimate_ai_agent.core.agent_runtime.contracts import (
    AgentRuntimeKind,
    AgentRuntimeRequest,
    DeterministicNoopAgentRuntimeAdapter,
)
from ultimate_ai_agent.core.capabilities import (
    Artifact,
    CapabilityAuthorityLevel,
    CapabilityKind,
    CapabilityManifest,
    CapabilityPrivacyLevel,
    CoordinationMode,
    RuntimePolicy,
    SafetyPolicy,
    SideEffectLevel,
    TaskEnvelope,
)
from ultimate_ai_agent.core.capabilities.enums import RiskLevel


DETERMINISTIC_SPECIALIST_CAPABILITY_ID = "cap:agent-runtime:deterministic-specialist"


class DeterministicAgentRuntimeSpecialistAdapter:
    def __init__(self, adapter: DeterministicNoopAgentRuntimeAdapter | None = None) -> None:
        self.adapter = adapter or DeterministicNoopAgentRuntimeAdapter()

    async def invoke(self, envelope: TaskEnvelope, context: dict) -> Artifact:
        request_ref = str(context.get("agent_runtime_request_ref") or f"agent-runtime-request:{envelope.task_id}")
        request = AgentRuntimeRequest(
            request_ref=request_ref,
            adapter_ref=self.adapter.adapter_ref,
            runtime_kind=AgentRuntimeKind.deterministic_local,
            capability_ref=context["capability_id"],
            safe_objective_summary="Deterministic specialist inspected safe task refs only.",
            safe_input_refs=[f"task-envelope-ref:{envelope.task_id}"],
            evidence_refs=[f"evidence-ref:agent-runtime-demo:{envelope.task_id}"],
            idempotency_ref=str(context.get("idempotency_ref") or f"idempotency-ref:agent-runtime-demo:{envelope.task_id}"),
        )
        result = self.adapter.invoke(request)
        return Artifact(
            producer_capability_id=context["capability_id"],
            kind="agent_runtime.deterministic_specialist",
            content={
                "request_ref": result.request_ref,
                "result_ref": result.result_ref,
                "safe_output_ref": result.safe_output_ref,
                "trace_refs": [trace.trace_ref for trace in result.trace_refs],
                "receipt_refs": list(result.receipt_refs),
                "execution_performed": result.execution_performed,
                "provider_runtime_performed": result.provider_runtime_performed,
                "memory_write_performed": result.memory_write_performed,
                "context_injection_performed": result.context_injection_performed,
                "connector_write_performed": result.connector_write_performed,
            },
            summary="Deterministic specialist returned safe refs without runtime authority.",
            citations_or_refs=[*result.evidence_refs, *result.receipt_refs],
            confidence=1.0,
            next_actions=["inspect_agent_runtime_demo_receipt_refs"],
            metadata={"agent_runtime_contract_only": True},
        )


def build_deterministic_specialist_manifest() -> CapabilityManifest:
    return CapabilityManifest(
        id=DETERMINISTIC_SPECIALIST_CAPABILITY_ID,
        version="1.0.0",
        kind=CapabilityKind.agent,
        name="Deterministic Agent Runtime Specialist",
        description="Contract-only in-process specialist proving safe agent-runtime adapter semantics.",
        tags=["agent-runtime", "deterministic", "specialist"],
        examples=["Use for local contract smoke tests of specialist-as-tool semantics."],
        anti_examples=["Do not use as live provider, SDK, browser, connector, memory, or shell authority."],
        input_schema={"type": "object", "properties": {"task_ref": {"type": "string"}}},
        output_schema={
            "type": "object",
            "required": ["safe_output_ref", "execution_performed"],
            "properties": {
                "safe_output_ref": {"type": "string"},
                "execution_performed": {"type": "boolean"},
            },
        },
        input_modes=["structured_ref"],
        output_modes=["artifact"],
        side_effects=SideEffectLevel.read,
        risk_level=RiskLevel.low,
        authority_level=CapabilityAuthorityLevel.read_only,
        deterministic=True,
        rollback_supported=False,
        receipt_required=True,
        privacy_level=CapabilityPrivacyLevel.local_private,
        evidence_required=True,
        memory_write_allowed=False,
        context_injection_allowed=False,
        provider_runtime_allowed=False,
        browser_runtime_allowed=False,
        connector_write_allowed=False,
        allowed_coordination_modes=[CoordinationMode.agent_as_tool],
        concurrency_safe=True,
        single_writer_required=False,
        runtime_policy=RuntimePolicy(deterministic=True),
        safety=SafetyPolicy(allow_parallel=False, max_risk_level=RiskLevel.low, max_side_effect_level=SideEffectLevel.read),
    )
