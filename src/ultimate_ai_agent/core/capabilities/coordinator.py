from __future__ import annotations

import asyncio
import time
from typing import Any

from ultimate_ai_agent.core.capabilities.approval import ApprovalAuthority
from ultimate_ai_agent.core.capabilities.catalog import render_compact_catalog
from ultimate_ai_agent.core.capabilities.enums import CapabilityHealthStatus, CoordinationMode, PolicyDecisionStatus
from ultimate_ai_agent.core.capabilities.locks import SingleWriterLockManager
from ultimate_ai_agent.core.capabilities.models import (
    Artifact,
    CapabilitySearchFilters,
    TaskEnvelope,
    TaskNode,
    TaskPlan,
    TelemetryEvent,
    is_mutating_side_effect,
    is_read_only_side_effect,
)
from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
from ultimate_ai_agent.core.capabilities.registry import CapabilityRegistry
from ultimate_ai_agent.core.capabilities.selection import LLMSelector, select_capabilities
from ultimate_ai_agent.core.capabilities.state import CoordinatorAuditEvent, CoordinatorStateStore, InMemoryCoordinatorStateStore
from ultimate_ai_agent.core.capabilities.telemetry import NoOpTelemetrySink, TelemetrySink


class PolicyDeniedError(RuntimeError):
    def __init__(self, reason_codes: list[str], safe_message: str) -> None:
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
        state_store: CoordinatorStateStore | None = None,
        approval_authority: ApprovalAuthority | None = None,
        single_writer_locks: SingleWriterLockManager | None = None,
        coordinator_capability_id: str = "coordinator:central",
    ) -> None:
        self.registry = registry
        self.policy_engine = policy_engine or PolicyEngine(approval_authority=approval_authority)
        self.telemetry = telemetry or NoOpTelemetrySink()
        self.llm_selector = llm_selector
        self.state_store = state_store or InMemoryCoordinatorStateStore()
        self.single_writer_locks = single_writer_locks or SingleWriterLockManager()
        self.coordinator_capability_id = coordinator_capability_id

    def plan(self, user_request: str, context: dict[str, Any] | None = None) -> TaskPlan:
        context = dict(context or {})
        trace_id = _trace_id(context)
        context["trace_id"] = trace_id
        catalog = self.registry.list_catalog(context)
        self._record_telemetry(
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
            self._record_telemetry(
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
            self._record_audit(
                "capability.selection_failed",
                trace_id=trace_id,
                status="denied",
                safe_summary="No capability could be selected for the coordinator request.",
                reason_codes=["NO_CAPABILITY_SELECTED"],
            )
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
        plan = TaskPlan(
            user_request=user_request,
            nodes=nodes,
            coordinator_capability_id=self.coordinator_capability_id,
            single_writer_node_id=single_writer_node_id,
            safe_summary="Coordinator-owned task plan with bounded capability envelopes.",
            reason_codes=reason_codes,
            metadata={"catalog_entry_count": len(catalog)},
        )
        self.state_store.save_plan(trace_id, plan)
        self._record_audit(
            "capability.plan_created",
            trace_id=trace_id,
            plan_id=plan.plan_id,
            status="planned",
            safe_summary="Coordinator created a bounded capability plan.",
            reason_codes=reason_codes,
            metadata={"node_count": len(nodes)},
        )
        return plan

    def execute(self, plan: TaskPlan, context: dict[str, Any] | None = None) -> Artifact:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.execute_async(plan, context or {}))
        raise RuntimeError("execute() cannot run inside an active event loop; use execute_async().")

    async def execute_async(self, plan: TaskPlan, context: dict[str, Any] | None = None) -> Artifact:
        context = dict(context or {})
        trace_id = _trace_id(context)
        context["trace_id"] = trace_id
        self.state_store.mark_run(trace_id, plan.plan_id, "running", plan.reason_codes)
        side_effect_decision = self.policy_engine.validate_side_effects(plan, self.registry)
        if not side_effect_decision.allowed:
            self._record_policy_denial(side_effect_decision.reason_codes, None, trace_id)
            self.state_store.mark_run(trace_id, plan.plan_id, "failed", side_effect_decision.reason_codes)
            raise PolicyDeniedError(side_effect_decision.reason_codes, side_effect_decision.safe_message)

        parallel_nodes = [node for node in plan.nodes if node.parallel_group]
        serial_nodes = [node for node in plan.nodes if not node.parallel_group]
        artifacts: list[Artifact] = []
        try:
            if parallel_nodes:
                artifacts.extend(await self._execute_parallel_read_nodes(parallel_nodes, context))
            for node in serial_nodes:
                artifacts.append(await self._execute_node(node, context))
            final_artifact = self._synthesize(plan, artifacts)
        except asyncio.CancelledError:
            self.state_store.mark_run(trace_id, plan.plan_id, "cancelled", ["COORDINATOR_EXECUTION_CANCELLED"])
            self._record_audit(
                "capability.execution_cancelled",
                trace_id=trace_id,
                plan_id=plan.plan_id,
                status="cancelled",
                safe_summary="Coordinator execution was cancelled.",
                reason_codes=["COORDINATOR_EXECUTION_CANCELLED"],
            )
            raise
        except Exception as exc:
            reason_codes = exc.reason_codes if isinstance(exc, PolicyDeniedError) else [type(exc).__name__]
            self.state_store.mark_run(trace_id, plan.plan_id, "failed", list(reason_codes))
            self._record_audit(
                "capability.execution_failed",
                trace_id=trace_id,
                plan_id=plan.plan_id,
                status="failed",
                safe_summary="Coordinator execution failed safely.",
                reason_codes=list(reason_codes),
            )
            if context.get("return_failure_artifact"):
                failure_artifact = Artifact(
                    producer_capability_id=self.coordinator_capability_id,
                    kind="coordinator.failure",
                    content={"plan_id": plan.plan_id, "reason_codes": list(reason_codes)},
                    summary="Coordinator execution failed safely with structured reason codes.",
                    confidence=0.0,
                    next_actions=["inspect_coordinator_audit"],
                )
                self.state_store.save_artifact(trace_id, plan.plan_id, failure_artifact)
                return failure_artifact
            raise
        self.state_store.save_artifact(trace_id, plan.plan_id, final_artifact)
        self.state_store.mark_run(trace_id, plan.plan_id, "succeeded", plan.reason_codes)
        self._record_audit(
            "capability.execution_succeeded",
            trace_id=trace_id,
            plan_id=plan.plan_id,
            status="succeeded",
            safe_summary="Coordinator execution completed with structured artifacts.",
            metadata={"artifact_count": len(artifacts)},
        )
        return final_artifact

    def run(self, user_request: str, context: dict[str, Any] | None = None) -> Artifact:
        context = dict(context or {})
        context["trace_id"] = _trace_id(context)
        plan = self.plan(user_request, context)
        return self.execute(plan, context)

    async def _execute_parallel_read_nodes(self, nodes: list[TaskNode], context: dict[str, Any]) -> list[Artifact]:
        if any(not is_read_only_side_effect(node.expected_side_effects) for node in nodes):
            raise PolicyDeniedError(["PARALLEL_NON_READ_ONLY_DENIED"], "Parallel fan-out is limited to read-only nodes.")
        results = await asyncio.gather(*(self._execute_node(node, context) for node in nodes), return_exceptions=True)
        artifacts: list[Artifact] = []
        for node, result in zip(nodes, results):
            if isinstance(result, BaseException):
                if not context.get("allow_partial_results"):
                    raise result
                artifacts.append(_failure_artifact(self.coordinator_capability_id, node, result))
                continue
            artifacts.append(result)
        return artifacts

    async def _execute_node(self, node: TaskNode, context: dict[str, Any]) -> Artifact:
        if is_mutating_side_effect(node.expected_side_effects):
            writer_key = str(context.get("single_writer_lock_key") or "capability-coordinator:single-writer")
            with self.single_writer_locks.acquire(writer_key) as lease_id:
                return await self._execute_node_locked(node, {**context, "single_writer_lease_id": lease_id})
        return await self._execute_node_locked(node, context)

    async def _execute_node_locked(self, node: TaskNode, context: dict[str, Any]) -> Artifact:
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
        health = adapter.health_check() if hasattr(adapter, "health_check") else None
        if health is not None and health.status == CapabilityHealthStatus.unhealthy:
            reason_codes = ["ADAPTER_HEALTH_CHECK_UNHEALTHY", *health.reason_codes]
            self._record_policy_denial(reason_codes, node.capability_id, context.get("trace_id"))
            raise PolicyDeniedError(reason_codes, "Capability adapter health check denied execution.")
        start = time.perf_counter()
        self._record_telemetry(
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
            artifact = await self._invoke_with_retries(adapter, manifest, node, execute_context)
        except asyncio.CancelledError:
            latency_ms = (time.perf_counter() - start) * 1000
            self._record_telemetry(
                TelemetryEvent(
                    event_name="capability.execution_cancelled",
                    trace_id=context.get("trace_id"),
                    capability_id=node.capability_id,
                    task_id=node.envelope.task_id,
                    success=False,
                    reason_codes=["CAPABILITY_EXECUTION_CANCELLED"],
                    latency_ms=latency_ms,
                )
            )
            raise
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            self._record_telemetry(
                TelemetryEvent(
                    event_name="capability.execution_failed",
                    trace_id=context.get("trace_id"),
                    capability_id=node.capability_id,
                    task_id=node.envelope.task_id,
                    success=False,
                    reason_codes=[type(exc).__name__],
                    latency_ms=latency_ms,
                )
            )
            await self._run_rollback_hook(node, execute_context, exc)
            raise
        if execute_context.get("single_writer_lease_id"):
            artifact.metadata["single_writer_lease_id"] = execute_context["single_writer_lease_id"]
        _validate_artifact_content(artifact, manifest.output_schema)
        latency_ms = (time.perf_counter() - start) * 1000
        self._record_telemetry(
            TelemetryEvent(
                event_name="capability.execution_completed",
                trace_id=context.get("trace_id"),
                capability_id=node.capability_id,
                task_id=node.envelope.task_id,
                success=True,
                latency_ms=latency_ms,
                estimated_cost_usd=manifest.runtime_policy.estimated_cost_usd,
                metadata={
                    "attempts": artifact.metadata.get("attempts"),
                    "single_writer_lease_id": execute_context.get("single_writer_lease_id"),
                },
            )
        )
        self._record_audit(
            "capability.node_completed",
            trace_id=context.get("trace_id"),
            task_id=node.envelope.task_id,
            capability_id=node.capability_id,
            status="succeeded",
            safe_summary="Capability node completed with a structured artifact.",
            metadata={"mode": node.mode.value},
        )
        return artifact

    async def _invoke_with_retries(self, adapter: Any, manifest: Any, node: TaskNode, context: dict[str, Any]) -> Artifact:
        attempts = max(1, manifest.runtime_policy.max_retries + 1)
        timeout_seconds = manifest.runtime_policy.timeout_seconds
        last_error: BaseException | None = None
        for attempt in range(1, attempts + 1):
            try:
                artifact = await asyncio.wait_for(adapter.invoke(node.envelope, context), timeout=timeout_seconds)
                artifact.metadata["attempts"] = attempt
                return artifact
            except asyncio.CancelledError:
                raise
            except TimeoutError as exc:
                last_error = exc
                reason_codes = ["CAPABILITY_TIMEOUT"]
            except Exception as exc:
                last_error = exc
                reason_codes = [type(exc).__name__]
            self._record_telemetry(
                TelemetryEvent(
                    event_name="capability.execution_attempt_failed",
                    trace_id=context.get("trace_id"),
                    capability_id=node.capability_id,
                    task_id=node.envelope.task_id,
                    success=False,
                    reason_codes=reason_codes,
                    metadata={"attempt": attempt, "max_attempts": attempts},
                )
            )
            if attempt >= attempts:
                break
        if last_error is None:
            raise RuntimeError("Capability execution failed without an exception.")
        raise last_error

    async def _run_rollback_hook(self, node: TaskNode, context: dict[str, Any], exc: BaseException) -> None:
        hooks = context.get("rollback_hooks") or {}
        hook = hooks.get(node.capability_id) if isinstance(hooks, dict) else None
        if hook is None:
            return
        try:
            result = hook(node.envelope, context, type(exc).__name__)
            if asyncio.iscoroutine(result):
                await result
            self._record_audit(
                "capability.rollback_hook_completed",
                trace_id=context.get("trace_id"),
                task_id=node.envelope.task_id,
                capability_id=node.capability_id,
                status="succeeded",
                safe_summary="Rollback hook completed after capability failure.",
            )
        except Exception as rollback_exc:
            self._record_audit(
                "capability.rollback_hook_failed",
                trace_id=context.get("trace_id"),
                task_id=node.envelope.task_id,
                capability_id=node.capability_id,
                status="failed",
                safe_summary="Rollback hook failed safely after capability failure.",
                reason_codes=[type(rollback_exc).__name__],
            )

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
        self._record_telemetry(
            TelemetryEvent(
                event_name="capability.policy_denied",
                trace_id=trace_id,
                capability_id=capability_id,
                success=False,
                reason_codes=reason_codes,
            )
        )
        self._record_audit(
            "capability.policy_denied",
            trace_id=trace_id,
            capability_id=capability_id,
            status="denied",
            safe_summary="Capability coordinator policy denied selection or execution.",
            reason_codes=reason_codes,
        )

    def _record_telemetry(self, event: TelemetryEvent) -> None:
        self.telemetry.record(event)
        self.state_store.record_telemetry_event(event)

    def _record_audit(
        self,
        event_name: str,
        *,
        status: str,
        safe_summary: str,
        trace_id: str | None = None,
        plan_id: str | None = None,
        task_id: str | None = None,
        capability_id: str | None = None,
        reason_codes: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.state_store.record_audit_event(
            CoordinatorAuditEvent(
                event_name=event_name,
                trace_id=trace_id,
                plan_id=plan_id,
                task_id=task_id,
                capability_id=capability_id,
                status=status,
                safe_summary=safe_summary,
                reason_codes=reason_codes or [],
                metadata=metadata or {},
            )
        )


def _average_confidence(artifacts: list[Artifact]) -> float | None:
    values = [artifact.confidence for artifact in artifacts if artifact.confidence is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _trace_id(context: dict[str, Any]) -> str:
    trace_id = context.get("trace_id")
    return str(trace_id) if trace_id else f"trace_{int(time.time() * 1000)}"


def _failure_artifact(coordinator_capability_id: str, node: TaskNode, exc: BaseException) -> Artifact:
    reason_codes = exc.reason_codes if isinstance(exc, PolicyDeniedError) else [type(exc).__name__]
    return Artifact(
        producer_capability_id=coordinator_capability_id,
        kind="coordinator.node_failure",
        content={"capability_id": node.capability_id, "reason_codes": list(reason_codes)},
        summary="Capability node failed safely during partial read fan-out.",
        confidence=0.0,
        next_actions=["inspect_capability_failure"],
        metadata={"task_id": node.envelope.task_id},
    )


def _validate_artifact_content(artifact: Artifact, output_schema: dict[str, Any]) -> None:
    if not output_schema or output_schema.get("type") != "object":
        return
    required = output_schema.get("required") or []
    if not required:
        return
    if not isinstance(artifact.content, dict):
        raise ValueError("ARTIFACT_CONTENT_SCHEMA_MISMATCH")
    missing = [key for key in required if key not in artifact.content]
    if missing:
        raise ValueError("ARTIFACT_CONTENT_REQUIRED_FIELD_MISSING")
