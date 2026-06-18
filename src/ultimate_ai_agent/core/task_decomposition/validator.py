from __future__ import annotations

from collections import defaultdict
from typing import Any

from pydantic import ValidationError

from ultimate_ai_agent.core.task_decomposition.contracts import (
    CapabilityContract,
    PlanValidationContext,
    PlanValidationIssue,
    PlanValidationResult,
    PlanValidationStatus,
    RiskLevel,
    TaskNode,
    TaskNodeStrategy,
    TaskPlan,
    permission_requires_approval,
)
from ultimate_ai_agent.core.task_decomposition.registry import CapabilityRegistry


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


class PlanValidator:
    def validate(
        self,
        plan: TaskPlan,
        registry: CapabilityRegistry,
        context: PlanValidationContext | None = None,
    ) -> PlanValidationResult:
        active_context = context or PlanValidationContext()
        issues: list[PlanValidationIssue] = []

        try:
            TaskPlan.model_validate(plan.model_dump())
        except (ValidationError, ValueError) as exc:
            issues.append(
                PlanValidationIssue(
                    reason_code="TASK_PLAN_SCHEMA_INVALID",
                    safe_message=str(exc).split("\n", 1)[0],
                )
            )

        node_by_id = {node.id: node for node in plan.nodes}
        if len(node_by_id) != len(plan.nodes):
            issues.append(
                PlanValidationIssue(
                    reason_code="DUPLICATE_TASK_NODE_ID",
                    safe_message="Task plan contains duplicate node ids.",
                )
            )

        if len(plan.nodes) > active_context.max_nodes:
            issues.append(
                PlanValidationIssue(
                    reason_code="TASK_PLAN_NODE_BUDGET_EXCEEDED",
                    safe_message="Task plan exceeds configured node budget.",
                )
            )
        if plan.max_iterations > active_context.max_iterations:
            issues.append(
                PlanValidationIssue(
                    reason_code="TASK_PLAN_ITERATION_BUDGET_EXCEEDED",
                    safe_message="Task plan exceeds configured iteration budget.",
                )
            )

        issues.extend(self._budget_issues(plan, active_context))
        issues.extend(self._dependency_issues(plan, node_by_id))
        issues.extend(self._capability_issues(plan, registry, node_by_id))
        issues.extend(self._input_binding_issues(plan, registry, node_by_id))
        issues.extend(self._final_success_issues(plan, node_by_id))

        reason_codes = _dedupe([issue.reason_code for issue in issues])
        blocking_codes = [
            code
            for code in reason_codes
            if code not in {"TASK_PLAN_APPROVAL_REQUIRED", "CAPABILITY_APPROVAL_REQUIRED"}
        ]
        approval_nodes = self._approval_required_node_ids(plan, registry)
        status = PlanValidationStatus.invalid if blocking_codes else PlanValidationStatus.valid
        valid = not blocking_codes
        if valid and approval_nodes:
            status = PlanValidationStatus.approval_required
            if "TASK_PLAN_APPROVAL_REQUIRED" not in reason_codes:
                reason_codes.append("TASK_PLAN_APPROVAL_REQUIRED")

        return PlanValidationResult(
            plan_id=plan.plan_id,
            valid=valid,
            status=status,
            reason_codes=reason_codes or ["TASK_PLAN_VALIDATED"],
            issues=issues,
            safe_message="Task plan validation completed.",
            approval_required_node_ids=approval_nodes,
        )

    def _budget_issues(self, plan: TaskPlan, context: PlanValidationContext) -> list[PlanValidationIssue]:
        issues: list[PlanValidationIssue] = []
        for key, max_value in context.max_budget.items():
            value = plan.budget.get(key)
            if isinstance(value, (int, float)) and value > max_value:
                issues.append(
                    PlanValidationIssue(
                        reason_code="TASK_PLAN_BUDGET_EXCEEDED",
                        safe_message=f"Task plan budget '{key}' exceeds configured maximum.",
                    )
                )
        return issues

    def _dependency_issues(
        self,
        plan: TaskPlan,
        node_by_id: dict[str, TaskNode],
    ) -> list[PlanValidationIssue]:
        issues: list[PlanValidationIssue] = []
        graph: dict[str, list[str]] = defaultdict(list)
        for node in plan.nodes:
            for dependency_id in node.depends_on:
                if dependency_id not in node_by_id:
                    issues.append(
                        PlanValidationIssue(
                            node_id=node.id,
                            reason_code="TASK_PLAN_DEPENDENCY_MISSING",
                            safe_message="Task node depends on an unknown node.",
                        )
                    )
                else:
                    graph[dependency_id].append(node.id)
            for fallback_id in node.fallback_node_ids:
                if fallback_id not in node_by_id:
                    issues.append(
                        PlanValidationIssue(
                            node_id=node.id,
                            reason_code="TASK_PLAN_FALLBACK_NODE_MISSING",
                            safe_message="Task node references an unknown fallback node.",
                        )
                    )

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> bool:
            if node_id in visiting:
                return True
            if node_id in visited:
                return False
            visiting.add(node_id)
            has_cycle = any(visit(next_node_id) for next_node_id in graph.get(node_id, []))
            visiting.remove(node_id)
            visited.add(node_id)
            return has_cycle

        if any(visit(node_id) for node_id in node_by_id):
            issues.append(
                PlanValidationIssue(
                    reason_code="TASK_PLAN_DEPENDENCY_CYCLE",
                    safe_message="Task plan dependency graph contains a cycle.",
                )
            )
        return issues

    def _capability_issues(
        self,
        plan: TaskPlan,
        registry: CapabilityRegistry,
        node_by_id: dict[str, TaskNode],
    ) -> list[PlanValidationIssue]:
        issues: list[PlanValidationIssue] = []
        for node in plan.nodes:
            for capability_id in node.candidate_capabilities:
                if registry.get(capability_id) is None:
                    issues.append(
                        PlanValidationIssue(
                            node_id=node.id,
                            reason_code="TASK_PLAN_CANDIDATE_CAPABILITY_MISSING",
                            safe_message="Task node references an unregistered candidate capability.",
                        )
                    )
            if node.selected_capability is None:
                continue
            contract = registry.get(node.selected_capability)
            if contract is None:
                issues.append(
                    PlanValidationIssue(
                        node_id=node.id,
                        reason_code="TASK_PLAN_SELECTED_CAPABILITY_MISSING",
                        safe_message="Task node selected an unregistered capability.",
                    )
                )
                continue
            if self._capability_needs_approval(contract) and not self._node_has_approval_gate(node, node_by_id):
                issues.append(
                    PlanValidationIssue(
                        node_id=node.id,
                        reason_code="TASK_PLAN_RISK_APPROVAL_GATE_MISSING",
                        safe_message="Risky capability node is missing a human approval gate.",
                    )
                )
        return issues

    def _input_binding_issues(
        self,
        plan: TaskPlan,
        registry: CapabilityRegistry,
        node_by_id: dict[str, TaskNode],
    ) -> list[PlanValidationIssue]:
        issues: list[PlanValidationIssue] = []
        for node in plan.nodes:
            issues.extend(self._binding_reference_issues(node, node_by_id))
            if not node.selected_capability:
                continue
            contract = registry.get(node.selected_capability)
            if contract is None:
                continue
            schema = contract.input_schema or {}
            if schema.get("type") == "object":
                for key in schema.get("required", []):
                    if key not in node.input_bindings:
                        issues.append(
                            PlanValidationIssue(
                                node_id=node.id,
                                reason_code="TASK_PLAN_INPUT_BINDING_MISSING",
                                safe_message="Task node input bindings do not satisfy the capability schema.",
                            )
                        )
        return issues

    def _binding_reference_issues(
        self,
        node: TaskNode,
        node_by_id: dict[str, TaskNode],
    ) -> list[PlanValidationIssue]:
        issues: list[PlanValidationIssue] = []

        def visit(value: Any) -> None:
            if isinstance(value, str) and value.startswith("$"):
                ref = value[1:].split(".", 1)[0]
                if ref not in node_by_id:
                    issues.append(
                        PlanValidationIssue(
                            node_id=node.id,
                            reason_code="TASK_PLAN_INPUT_REF_MISSING",
                            safe_message="Task node input binding references an unknown node output.",
                        )
                    )
                elif ref not in set(node.depends_on):
                    issues.append(
                        PlanValidationIssue(
                            node_id=node.id,
                            reason_code="TASK_PLAN_INPUT_REF_NOT_DEPENDENCY",
                            safe_message="Task node input binding references a node that is not a declared dependency.",
                        )
                    )
            elif isinstance(value, dict):
                for nested in value.values():
                    visit(nested)
            elif isinstance(value, list):
                for nested in value:
                    visit(nested)

        visit(node.input_bindings)
        return issues

    def _final_success_issues(
        self,
        plan: TaskPlan,
        node_by_id: dict[str, TaskNode],
    ) -> list[PlanValidationIssue]:
        if not plan.final_success_criteria:
            return [
                PlanValidationIssue(
                    reason_code="TASK_PLAN_FINAL_SUCCESS_CRITERIA_MISSING",
                    safe_message="Task plan must declare final success criteria.",
                )
            ]
        depended_on = {dependency for node in plan.nodes for dependency in node.depends_on}
        terminal_nodes = [node for node in plan.nodes if node.id not in depended_on]
        if not any(node.success_criteria for node in terminal_nodes):
            return [
                PlanValidationIssue(
                    reason_code="TASK_PLAN_TERMINAL_SUCCESS_CRITERIA_MISSING",
                    safe_message="At least one terminal node must declare success criteria.",
                )
            ]
        return []

    def _approval_required_node_ids(self, plan: TaskPlan, registry: CapabilityRegistry) -> list[str]:
        node_ids: list[str] = []
        for node in plan.nodes:
            contract = registry.get(node.selected_capability) if node.selected_capability else None
            if node.requires_approval or (contract is not None and self._capability_needs_approval(contract)):
                node_ids.append(node.id)
        return sorted(set(node_ids))

    def _node_has_approval_gate(self, node: TaskNode, node_by_id: dict[str, TaskNode]) -> bool:
        if node.requires_approval:
            return True
        for dependency_id in node.depends_on:
            dependency = node_by_id.get(dependency_id)
            if dependency and dependency.decomposition_strategy == TaskNodeStrategy.human_approval:
                return True
        return False

    def _capability_needs_approval(self, contract: CapabilityContract) -> bool:
        return (
            contract.card.requires_approval
            or contract.card.risk_level in {RiskLevel.high, RiskLevel.critical}
            or any(permission_requires_approval(permission) for permission in contract.required_permissions)
        )
