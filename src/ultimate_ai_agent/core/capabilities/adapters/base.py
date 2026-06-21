from __future__ import annotations

import inspect
from typing import Any, Callable, Protocol, runtime_checkable

from ultimate_ai_agent.core.capabilities.enums import CapabilityHealthStatus
from ultimate_ai_agent.core.capabilities.models import Artifact, CapabilityHealthReport, TaskEnvelope


@runtime_checkable
class CapabilityAdapter(Protocol):
    async def invoke(self, envelope: TaskEnvelope, context: dict[str, Any]) -> Artifact:
        ...

    def health_check(self) -> CapabilityHealthReport:
        ...


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


class CallableCapabilityAdapter:
    def __init__(
        self,
        capability_id: str,
        callable_obj: Callable[..., Any],
        *,
        artifact_kind: str,
    ) -> None:
        self.capability_id = capability_id
        self.callable_obj = callable_obj
        self.artifact_kind = artifact_kind

    async def invoke(self, envelope: TaskEnvelope, context: dict[str, Any]) -> Artifact:
        result = await _maybe_await(self.callable_obj(envelope, context))
        if isinstance(result, Artifact):
            return result
        return Artifact(
            producer_capability_id=self.capability_id,
            kind=self.artifact_kind,
            content=result,
            summary=str(result)[:240] if result is not None else "Capability completed with no content.",
        )

    def health_check(self) -> CapabilityHealthReport:
        return CapabilityHealthReport(
            capability_id=self.capability_id,
            status=CapabilityHealthStatus.healthy,
            reason_codes=["CALLABLE_ADAPTER_AVAILABLE"],
        )


class ToolAdapter(CallableCapabilityAdapter):
    def __init__(self, capability_id: str, tool_callable: Callable[..., Any]) -> None:
        super().__init__(capability_id, tool_callable, artifact_kind="tool.result")


class AgentAdapter(CallableCapabilityAdapter):
    def __init__(self, capability_id: str, agent_callable: Callable[..., Any]) -> None:
        super().__init__(capability_id, agent_callable, artifact_kind="agent.result")


class WorkflowAdapter(CallableCapabilityAdapter):
    def __init__(self, capability_id: str, workflow_callable: Callable[..., Any]) -> None:
        super().__init__(capability_id, workflow_callable, artifact_kind="workflow.result")


class HandoffAdapter(CallableCapabilityAdapter):
    def __init__(self, capability_id: str, handoff_callable: Callable[..., Any]) -> None:
        super().__init__(capability_id, handoff_callable, artifact_kind="handoff.next_turn")


class ReviewerAdapter(CallableCapabilityAdapter):
    def __init__(self, capability_id: str, reviewer_callable: Callable[..., Any]) -> None:
        super().__init__(capability_id, reviewer_callable, artifact_kind="review.result")


class HumanGateAdapter:
    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id

    async def invoke(self, envelope: TaskEnvelope, context: dict[str, Any]) -> Artifact:
        approval_ref = context.get("approval_ref")
        summary = "Human approval gate satisfied." if approval_ref else "Human approval is required."
        return Artifact(
            producer_capability_id=self.capability_id,
            kind="human_gate.decision",
            content={"approval_ref": approval_ref, "approved": bool(approval_ref)},
            summary=summary,
            next_actions=[] if approval_ref else ["collect_human_approval"],
        )

    def health_check(self) -> CapabilityHealthReport:
        return CapabilityHealthReport(
            capability_id=self.capability_id,
            status=CapabilityHealthStatus.healthy,
            reason_codes=["HUMAN_GATE_AVAILABLE"],
        )


def wrap_tool(capability_id: str, tool_callable: Callable[..., Any]) -> ToolAdapter:
    return ToolAdapter(capability_id, tool_callable)


def wrap_agent(capability_id: str, agent_callable: Callable[..., Any]) -> AgentAdapter:
    return AgentAdapter(capability_id, agent_callable)
