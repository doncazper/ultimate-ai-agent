from __future__ import annotations

import asyncio
from typing import Any

from ultimate_ai_agent.core.task_decomposition.contracts import (
    CapabilityCallContext,
    CapabilityCallStatus,
    DAGExecutionResult,
    DAGExecutionStatus,
    NodeExecutionRecord,
    NodeExecutionStatus,
    TaskNode,
    TaskNodeStrategy,
    TaskPlan,
)
from ultimate_ai_agent.core.task_decomposition.registry import CapabilityRegistry
from ultimate_ai_agent.core.task_decomposition.validator import PlanValidator
from ultimate_ai_agent.core.time import utc_now


class DAGExecutor:
    def __init__(
        self,
        registry: CapabilityRegistry,
        validator: PlanValidator | None = None,
        *,
        parallel: bool = True,
    ):
        self.registry = registry
        self.validator = validator or PlanValidator()
        self.parallel = parallel

    async def execute(
        self,
        plan: TaskPlan,
        context: CapabilityCallContext | None = None,
    ) -> DAGExecutionResult:
        active_context = context or CapabilityCallContext()
        validation = self.validator.validate(plan, self.registry)
        if not validation.valid:
            return DAGExecutionResult(
                plan_id=plan.plan_id,
                status=DAGExecutionStatus.validation_failed,
                node_records=[],
                reason_codes=validation.reason_codes,
                safe_summary="Task plan failed validation before execution.",
            )

        node_by_id = {node.id: node for node in plan.nodes}
        records: dict[str, NodeExecutionRecord] = {
            node.id: NodeExecutionRecord(
                node_id=node.id,
                status=NodeExecutionStatus.pending,
                selected_capability=node.selected_capability,
                safe_summary="Task node is pending.",
            )
            for node in plan.nodes
        }
        outputs: dict[str, dict[str, Any]] = {}
        remaining = set(node_by_id)
        fallback_ready: set[str] = set()
        repair_requested = False
        repair_node_ids: list[str] = []
        semaphores = self._capability_semaphores(plan)

        while remaining:
            ready_ids = self._ready_node_ids(node_by_id, records, remaining, fallback_ready)
            if not ready_ids:
                self._skip_unreachable_nodes(node_by_id, records, remaining)
                if not ready_ids and all(records[node_id].status != NodeExecutionStatus.pending for node_id in remaining):
                    remaining.clear()
                    break
                break

            batch_ids = ready_ids if self.parallel else ready_ids[:1]
            tasks = [
                self._run_node(node_by_id[node_id], outputs, active_context, semaphores)
                for node_id in batch_ids
            ]
            batch_records = await asyncio.gather(*tasks)
            for record in batch_records:
                records[record.node_id] = record
                remaining.discard(record.node_id)
                if record.status == NodeExecutionStatus.succeeded:
                    outputs[record.node_id] = record.output
                elif record.status == NodeExecutionStatus.failed:
                    node = node_by_id[record.node_id]
                    if node.fallback_node_ids:
                        repair_requested = True
                        repair_node_ids.extend(node.fallback_node_ids)
                        fallback_ready.update(node.fallback_node_ids)

        ordered_records = [records[node.id] for node in sorted(plan.nodes, key=lambda item: item.id)]
        status = self._result_status(ordered_records)
        return DAGExecutionResult(
            plan_id=plan.plan_id,
            status=status,
            node_records=ordered_records,
            outputs=outputs,
            reason_codes=self._result_reason_codes(status, ordered_records),
            safe_summary=self._result_summary(status),
            repair_requested=repair_requested,
            repair_node_ids=sorted(set(repair_node_ids)),
        )

    def _capability_semaphores(self, plan: TaskPlan) -> dict[str, asyncio.Semaphore]:
        semaphores: dict[str, asyncio.Semaphore] = {}
        for node in plan.nodes:
            if not node.selected_capability or node.selected_capability in semaphores:
                continue
            contract = self.registry.get(node.selected_capability)
            if contract is not None:
                semaphores[node.selected_capability] = asyncio.Semaphore(contract.concurrency_limit)
        return semaphores

    def _ready_node_ids(
        self,
        node_by_id: dict[str, TaskNode],
        records: dict[str, NodeExecutionRecord],
        remaining: set[str],
        fallback_ready: set[str],
    ) -> list[str]:
        ready: list[str] = []
        for node_id in sorted(remaining):
            node = node_by_id[node_id]
            if node_id in fallback_ready:
                ready.append(node_id)
                continue
            dependency_statuses = [records[dependency_id].status for dependency_id in node.depends_on]
            if dependency_statuses and not all(status == NodeExecutionStatus.succeeded for status in dependency_statuses):
                continue
            ready.append(node_id)
        return ready

    async def _run_node(
        self,
        node: TaskNode,
        outputs: dict[str, dict[str, Any]],
        context: CapabilityCallContext,
        semaphores: dict[str, asyncio.Semaphore],
    ) -> NodeExecutionRecord:
        started = utc_now()
        if node.requires_approval and not self._approval_available(node, context):
            return NodeExecutionRecord(
                node_id=node.id,
                status=NodeExecutionStatus.awaiting_approval,
                selected_capability=node.selected_capability,
                attempts=0,
                reason_codes=["TASK_NODE_APPROVAL_REQUIRED"],
                safe_summary="Task node is awaiting human approval.",
                started_at=started,
                completed_at=utc_now(),
            )

        if node.selected_capability is None:
            return self._complete_internal_node(node, started)

        args = self._resolve_bindings(node.input_bindings, outputs)
        validation = self.registry.validate_call(node.selected_capability, args, context)
        if not validation.valid:
            status = (
                NodeExecutionStatus.awaiting_approval
                if validation.status == CapabilityCallStatus.approval_required
                else NodeExecutionStatus.failed
            )
            return NodeExecutionRecord(
                node_id=node.id,
                status=status,
                selected_capability=node.selected_capability,
                attempts=0,
                reason_codes=validation.reason_codes,
                safe_summary=validation.safe_message,
                started_at=started,
                completed_at=utc_now(),
            )

        contract = self.registry.get(node.selected_capability)
        max_attempts = int((contract.retry_policy if contract else {}).get("max_attempts", 1))
        backoff_s = float((contract.retry_policy if contract else {}).get("backoff_s", 0.0))
        attempts = 0
        last_reason_codes: list[str] = []
        last_summary = "Task node did not run."
        last_output: dict[str, Any] = {}
        semaphore = semaphores.get(node.selected_capability, asyncio.Semaphore(1))
        async with semaphore:
            for attempt in range(max(1, max_attempts)):
                attempts = attempt + 1
                result = await self.registry.invoke(node.selected_capability, args, context)
                last_reason_codes = result.reason_codes
                last_summary = result.safe_summary
                last_output = result.output
                if result.status == CapabilityCallStatus.succeeded and self._output_satisfies_node(node, result.output):
                    return NodeExecutionRecord(
                        node_id=node.id,
                        status=NodeExecutionStatus.succeeded,
                        selected_capability=node.selected_capability,
                        attempts=attempts,
                        output=result.output,
                        observations=result.observations,
                        reason_codes=result.reason_codes,
                        safe_summary="Task node completed successfully.",
                        started_at=started,
                        completed_at=utc_now(),
                    )
                if attempt + 1 < max_attempts and backoff_s > 0:
                    await asyncio.sleep(backoff_s)

        return NodeExecutionRecord(
            node_id=node.id,
            status=NodeExecutionStatus.failed,
            selected_capability=node.selected_capability,
            attempts=attempts,
            output=last_output,
            observations=[last_summary],
            reason_codes=last_reason_codes or ["TASK_NODE_FAILED"],
            safe_summary="Task node failed after retry policy was exhausted.",
            started_at=started,
            completed_at=utc_now(),
        )

    def _complete_internal_node(self, node: TaskNode, started) -> NodeExecutionRecord:
        if node.decomposition_strategy == TaskNodeStrategy.human_approval:
            output = {"success": True, "approval_gate": True}
            summary = "Human approval or clarification gate completed."
        elif node.decomposition_strategy == TaskNodeStrategy.evaluate:
            output = {"success": True, "evaluated": True}
            summary = "Evaluation node completed with safe structured summary."
        else:
            output = {"success": True}
            summary = "Internal task node completed."
        return NodeExecutionRecord(
            node_id=node.id,
            status=NodeExecutionStatus.succeeded,
            selected_capability=None,
            attempts=1,
            output=output,
            observations=[summary],
            reason_codes=["TASK_NODE_INTERNAL_COMPLETED"],
            safe_summary=summary,
            started_at=started,
            completed_at=utc_now(),
        )

    def _approval_available(self, node: TaskNode, context: CapabilityCallContext) -> bool:
        if node.selected_capability:
            return context.is_approved(node.selected_capability) or node.selected_capability in context.approval_refs
        return node.id in set(context.approved_capability_ids)

    def _resolve_bindings(self, value: Any, outputs: dict[str, dict[str, Any]]) -> Any:
        if isinstance(value, str) and value.startswith("$"):
            ref = value[1:]
            node_id, _, key = ref.partition(".")
            output = outputs.get(node_id, {})
            if not key:
                return output
            return output.get(key)
        if isinstance(value, dict):
            return {key: self._resolve_bindings(nested, outputs) for key, nested in value.items()}
        if isinstance(value, list):
            return [self._resolve_bindings(item, outputs) for item in value]
        return value

    def _output_satisfies_node(self, node: TaskNode, output: dict[str, Any]) -> bool:
        if output.get("success") is False or output.get("ok") is False:
            return False
        status = str(output.get("status", "")).lower()
        if status in {"failed", "error", "denied"}:
            return False
        return True

    def _skip_unreachable_nodes(
        self,
        node_by_id: dict[str, TaskNode],
        records: dict[str, NodeExecutionRecord],
        remaining: set[str],
    ) -> None:
        for node_id in list(remaining):
            node = node_by_id[node_id]
            dependency_statuses = [records[dependency_id].status for dependency_id in node.depends_on]
            if any(status == NodeExecutionStatus.failed for status in dependency_statuses):
                records[node_id] = NodeExecutionRecord(
                    node_id=node_id,
                    status=NodeExecutionStatus.skipped,
                    selected_capability=node.selected_capability,
                    attempts=0,
                    reason_codes=["TASK_NODE_DEPENDENCY_FAILED"],
                    safe_summary="Task node skipped because a dependency failed.",
                    completed_at=utc_now(),
                )

    def _result_status(self, records: list[NodeExecutionRecord]) -> DAGExecutionStatus:
        statuses = {record.status for record in records}
        if NodeExecutionStatus.awaiting_approval in statuses:
            return DAGExecutionStatus.awaiting_approval
        if NodeExecutionStatus.failed in statuses or NodeExecutionStatus.skipped in statuses:
            return DAGExecutionStatus.failed
        return DAGExecutionStatus.succeeded

    def _result_reason_codes(
        self,
        status: DAGExecutionStatus,
        records: list[NodeExecutionRecord],
    ) -> list[str]:
        if status == DAGExecutionStatus.succeeded:
            return ["DAG_EXECUTION_SUCCEEDED"]
        if status == DAGExecutionStatus.awaiting_approval:
            return ["DAG_EXECUTION_AWAITING_APPROVAL"]
        if status == DAGExecutionStatus.validation_failed:
            return ["DAG_EXECUTION_VALIDATION_FAILED"]
        reasons: list[str] = ["DAG_EXECUTION_FAILED"]
        for record in records:
            if record.status in {NodeExecutionStatus.failed, NodeExecutionStatus.skipped}:
                reasons.extend(record.reason_codes)
        return list(dict.fromkeys(reasons))

    def _result_summary(self, status: DAGExecutionStatus) -> str:
        if status == DAGExecutionStatus.succeeded:
            return "DAG plan execution completed successfully."
        if status == DAGExecutionStatus.awaiting_approval:
            return "DAG plan execution paused for human approval."
        if status == DAGExecutionStatus.validation_failed:
            return "DAG plan execution was blocked by validation."
        return "DAG plan execution completed with failures."
