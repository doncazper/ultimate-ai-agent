from __future__ import annotations

import asyncio
import time
from typing import Any

from ultimate_ai_agent.core.capabilities.catalog import render_compact_catalog
from ultimate_ai_agent.core.capabilities.enums import CoordinationMode, PolicyDecisionStatus
from ultimate_ai_agent.core.capabilities.models import (
    Artifact,
    CapabilitySearchFilters,
    TaskEnvelope,
    TaskNode,
    TaskPlan,
    TelemetryEvent,
    is_read_only_side_effect,
)
from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
from ultimate_ai_agent.core.capabilities.registry import CapabilityRegistry
from ultimate_ai_agent.core.capabilities.selection import LLMSelector, select_capabilities
from ultimate_ai_agent.core.capabilities.telemetry import NoOpTelemetrySink, TelemetrySink


class PolicyDeniedError(RuntimeError):
    def __init__(self, reason_codes: list[str], safe_message: str):
        super().__init__(safe_message)
        self.reason_codes = reason_codes
        self.safe_message = safe_message


class Coordinator:
    def __init__(
        self,
        registry: CapabilityRegistry,
        *,
        policy_engine: PolicyEngine | None = None,
        telemetry: TelemetrySink | None = None,
        llm_selector: LLMSelector | None = None,
        coordinator_capability_id: str = "coordinator:central",
    ):
        self.registry = registry
        self.policy_engine = policy_engine or PolicyEngine()
        self.telemetry = telemetry or NoOpTelemetrySink()
        self.llm_selector = llm_selector
        self.coordinator_capability_id = coordinator_capability_id

    def plan(self, user_request: str, context: dict[str, Any] | None = None) -> TaskPlan:
        context = context or {}
        trace_id = context.get("trace_id")
        catalog = self.registry.list_catalog(context)
        self.telemetry.record(
            TelemetryEvent(
                event_name="capability.catalog_rendered",
                trace_id=trace_id,
                success=True,
                metadata={"catalog_size": len(catalog), "catalog": render_compact_catalog(catalog, max_entries=10)},
            )
        )
        explicit_ids = list(context.get("capability_ids") or context.get("selected_capability_ids") or [])
        if explicit_ids:
            selected_ids = explicit_ids
            reason_codes = ["EXPLICIT_CAPABILITY_IDS_SELECTED"]
        else:
            filters = context.get("search_filters")
            if isinstance(filters, dict):
                filters = CapabilitySearchFilters(**filters)
            selection = select_capabilities(
                user_request,
                self.registry,
                context,
                filters,
                llm_selector=self.llm_selector,
            )
            selected_ids = selection.selected_capability_ids
            reason_codes = list(selection.reason_codes)
            self.telemetry.record(
                TelemetryEvent(
                    event_name="capability.selection_completed",
                    trace_id=trace_id,
                    success=bool(selected_ids),
                    reason_codes=selection.reason_codes,
                    metadata={
                        "selected_capability_ids": selected_ids,
                        "candidate_scores": selection.candidate_scores,
                        "selector_kind": selection.selector_kind,
                    },
                )
            )
        if not selected_ids:
            raise PolicyDeniedError(["NO_CAPABILITY_SELECTED"], "No capability could be selected for the request.")

        parallel_requested = bool(context.get("parallel_read_fanout")) or len(selected_ids) > 1
        nodes: list[TaskNode] = []
        for index, capability_id in enumerate(selected_ids):
            manifest = self.registry.load_manifest(capability_id)
            selection_decision = self.policy_engine.can_select(manifest, context)
            if not selection_decision.allowed:
                self._record_policy_denial(selection_decision.reason_codes, capability_id, trace_id)
                raise PolicyDeniedError(selection_decision.reason_codes, selection_decision.safe_message)
            mode = self._coordination_mode(manifest.allowed_coordination_modes, parallel_requested)
            envelope = self._build_envelope(user_request, manifest.id, context)
            nodes.append(
                TaskNode(
                    node_id=f"node_{index + 1}_{manifest.id.replace(':', '_').replace('.', '_')}",
                    capability_id=manifest.id,
                    mode=mode,
                    envelope=envelope,
                    parallel_group="read_fanout" if mode == CoordinationMode.parallel_read_fanout else None,
                    expected_side_effects=manifest.side_effects,
                    risk_level=manifest.risk_level,
                    requires_approval=bool(manifest.approval_required),
                    approval_ref=context.get("approval_ref"),
                )
            )

        single_writer_node_id = next((node.node_id for node in nodes if not is_read_only_side_effect(node.expected_side_effects)), None)
        return TaskPlan(
            user_request=user_request,
            nodes=nodes,
            coordinator_capability_id=self.coordinator_capability_id,
            single_writer_node_id=single_writer_node_id,
            safe_summary="Coordinator-owned task plan with bounded capability envelopes.",
            reason_codes=reason_codes,
            metadata={"catalog_entry_count": len(catalog)},
        )

    def execute(self, plan: TaskPlan, context: dict[str, Any] | None = None) -> Artifact:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.execute_async(plan, context or {}))
        raise RuntimeError("execute() cannot run inside an active event loop; use execute_async().")

    async def execute_async(self, plan: TaskPlan, context: dict[str, Any] | None = None) -> Artifact:
        context = context or {}
        trace_id = context.get("trace_id")
        side_effect_decision = self.policy_engine.validate_side_effects(plan, self.registry)
        if not side_effect_decision.allowed:
            self._record_policy_denial(side_effect_decision.reason_codes, None, trace_id)
            raise PolicyDeniedError(side_effect_decision.reason_codes, side_effect_decision.safe_message)

        parallel_nodes = [node for node in plan.nodes if node.parallel_group]
        serial_nodes = [node for node in plan.nodes if not node.parallel_group]
        artifacts: list[Artifact] = []
        if parallel_nodes:
            artifacts.extend(await self._execute_parallel_read_nodes(parallel_nodes, context))
        for node in serial_nodes:
            artifacts.append(await self._execute_node(node, context))
        return self._synthesize(plan, artifacts)

    def run(self, user_request: str, context: dict[str, Any] | None = None) -> Artifact:
        context = context or {}
        plan = self.plan(user_request, context)
        return self.execute(plan, context)

    async def _execute_parallel_read_nodes(self, nodes: list[TaskNode], context: dict[str, Any]) -> list[Artifact]:
        if any(not is_read_only_side_effect(node.expected_side_effects) for node in nodes):
            raise PolicyDeniedError(["PARALLEL_NON_READ_ONLY_DENIED"], "Parallel fan-out is limited to read-only nodes.")
        return list(await asyncio.gather(*(self._execute_node(node, context) for node in nodes)))

    async def _execute_node(self, node: TaskNode, context: dict[str, Any]) -> Artifact:
        manifest = self.registry.load_manifest(node.capability_id)
        execute_context = {
            **context,
            "coordination_mode": node.mode.value,
            "capability_id": node.capability_id,
        }
        decision = self.policy_engine.can_execute(manifest, node.envelope, execute_context)
        if decision.status == PolicyDecisionStatus.approval_required:
            self._record_policy_denial(decision.reason_codes, node.capability_id, context.get("trace_id"))
            raise PolicyDeniedError(decision.reason_codes, decision.safe_message)
        if not decision.allowed:
            self._record_policy_denial(decision.reason_codes, node.capability_id, context.get("trace_id"))
            raise PolicyDeniedError(decision.reason_codes, decision.safe_message)
        adapter = self.registry.resolve_adapter(node.capability_id)
        start = time.perf_counter()
        self.telemetry.record(
            TelemetryEvent(
                event_name="capability.execution_started",
                trace_id=context.get("trace_id"),
                capability_id=node.capability_id,
                task_id=node.envelope.task_id,
                estimated_cost_usd=manifest.runtime_policy.estimated_cost_usd,
                metadata={"mode": node.mode.value},
            )
        )
        try:
            artifact = await adapter.invoke(node.envelope, execute_context)
        except Exception:
            latency_ms = (time.perf_counter() - start) * 1000
            self.telemetry.record(
                TelemetryEvent(
                    event_name="capability.execution_failed",
                    trace_id=context.get("trace_id"),
                    capability_id=node.capability_id,
                    task_id=node.envelope.task_id,
                    success=False,
                    reason_codes=["ADAPTER_INVOCATION_FAILED"],
                    latency_ms=latency_ms,
                )
            )
            raise
        latency_ms = (time.perf_counter() - start) * 1000
        self.telemetry.record(
            TelemetryEvent(
                event_name="capability.execution_completed",
                trace_id=context.get("trace_id"),
                capability_id=node.capability_id,
                task_id=node.envelope.task_id,
                success=True,
                latency_ms=latency_ms,
                estimated_cost_usd=manifest.runtime_policy.estimated_cost_usd,
            )
        )
        return artifact

    def _synthesize(self, plan: TaskPlan, artifacts: list[Artifact]) -> Artifact:
        if len(artifacts) == 1 and not plan.final_synthesis_required:
            return artifacts[0]
        return Artifact(
            producer_capability_id=self.coordinator_capability_id,
            kind="coordinator.final",
            content=[artifact.model_dump(mode="json") for artifact in artifacts],
            summary="Coordinator synthesized bounded capability artifacts.",
            citations_or_refs=[ref for artifact in artifacts for ref in artifact.citations_or_refs],
            confidence=_average_confidence(artifacts),
            side_effects_performed=[effect for artifact in artifacts for effect in artifact.side_effects_performed],
            next_actions=[action for artifact in artifacts for action in artifact.next_actions],
            metadata={"plan_id": plan.plan_id, "artifact_count": len(artifacts)},
        )

    def _build_envelope(
        self,
        user_request: str,
        capability_id: str,
        context: dict[str, Any],
    ) -> TaskEnvelope:
        return TaskEnvelope(
            user_request=user_request,
            objective=context.get("objective") or user_request,
            background=context.get("background"),
            scope=list(context.get("scope") or [capability_id]),
            out_of_scope=list(context.get("out_of_scope") or []),
            selected_capability_ids=[capability_id],
            allowed_tool_ids=list(context.get("allowed_tool_ids") or []),
            required_output_schema=context.get("required_output_schema"),
            acceptance_criteria=list(context.get("acceptance_criteria") or []),
            budget=dict(context.get("budget") or {}),
            context=dict(context.get("relevant_context") or {}),
            memory_refs=list(context.get("memory_refs") or []),
            parent_trace_id=context.get("trace_id"),
        )

    def _coordination_mode(
        self,
        allowed_modes: list[CoordinationMode],
        parallel_requested: bool,
    ) -> CoordinationMode:
        if parallel_requested and CoordinationMode.parallel_read_fanout in allowed_modes:
            return CoordinationMode.parallel_read_fanout
        for preferred in [
            CoordinationMode.direct_tool,
            CoordinationMode.agent_as_tool,
            CoordinationMode.workflow_node,
            CoordinationMode.reviewer,
            CoordinationMode.human_gate,
            CoordinationMode.handoff,
        ]:
            if preferred in allowed_modes:
                return preferred
        return allowed_modes[0]

    def _record_policy_denial(
        self,
        reason_codes: list[str],
        capability_id: str | None,
        trace_id: str | None,
    ) -> None:
        self.telemetry.record(
            TelemetryEvent(
                event_name="capability.policy_denied",
                trace_id=trace_id,
                capability_id=capability_id,
                success=False,
                reason_codes=reason_codes,
            )
        )


def _average_confidence(artifacts: list[Artifact]) -> float | None:
    values = [artifact.confidence for artifact in artifacts if artifact.confidence is not None]
    if not values:
        return None
    return sum(values) / len(values)
