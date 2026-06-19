from __future__ import annotations

import hashlib
from typing import Any

from ultimate_ai_agent.core.task_decomposition.contracts import (
    AmbiguityLevel,
    CapabilityRoutingCard,
    ComplexityLevel,
    PlanValidationContext,
    PlanValidationResult,
    RiskLevel,
    TaskIntent,
    TaskNode,
    TaskNodeStrategy,
    TaskPlan,
    risk_rank,
)
from ultimate_ai_agent.core.task_decomposition.enums import CapabilityKind, PlanStrategy
from ultimate_ai_agent.core.task_decomposition.registry import CapabilityRegistry
from ultimate_ai_agent.core.task_decomposition.validator import PlanValidator


class TaskDecomposer:
    def __init__(self, registry: CapabilityRegistry, validator: PlanValidator | None = None):
        self.registry = registry
        self.validator = validator or PlanValidator()

    def classify_intent(self, raw_request: str, context: dict[str, Any] | None = None) -> TaskIntent:
        request = raw_request.strip()
        lowered = request.lower()
        constraints = self._extract_constraints(request)
        assumptions = ["Use only registered capabilities returned by the capability registry."]
        ambiguity = self._ambiguity_level(lowered)
        complexity = self._complexity_level(lowered)
        risk = self._risk_level(lowered)
        expected_output = self._expected_output(lowered)
        success_criteria = self._success_criteria(expected_output)
        requires_clarification = not request or ambiguity == AmbiguityLevel.high and "clarify" in lowered
        questions = ["What exact outcome should be optimized first?"] if requires_clarification else []
        budget = dict((context or {}).get("budget", {}))

        return TaskIntent(
            goal=self._goal_summary(request),
            raw_request=request,
            constraints=constraints,
            assumptions=assumptions,
            ambiguity_level=ambiguity,
            complexity=complexity,
            risk_level=risk,
            expected_output=expected_output,
            success_criteria=success_criteria,
            budget=budget,
            requires_clarification=requires_clarification,
            clarification_questions=questions,
        )

    def retrieve_capabilities(self, intent: TaskIntent) -> list[CapabilityRoutingCard]:
        query = " ".join([intent.goal, intent.expected_output or "", *intent.constraints, *intent.success_criteria])
        risk_max = RiskLevel.critical if risk_rank(intent.risk_level) >= risk_rank(RiskLevel.high) else RiskLevel.medium
        candidates = self.registry.search(query, risk_max=risk_max, top_k=8)
        return self.registry.rank_for_task(intent, candidates)

    def select_strategy(self, intent: TaskIntent, candidates: list[CapabilityRoutingCard]) -> PlanStrategy:
        if intent.requires_clarification:
            return PlanStrategy.human_in_loop
        if candidates and candidates[0].kind in {CapabilityKind.skill, CapabilityKind.workflow}:
            return PlanStrategy.skill_reuse
        if intent.ambiguity_level == AmbiguityLevel.high or intent.risk_level in {RiskLevel.high, RiskLevel.critical}:
            return PlanStrategy.tree_search
        lowered = intent.raw_request.lower()
        if any(marker in lowered for marker in ["interactive", "tool feedback", "iterate", "observe", "react"]):
            return PlanStrategy.react_loop
        if intent.complexity in {ComplexityLevel.complex, ComplexityLevel.long_horizon} or any(
            marker in lowered for marker in ["parallel", "concurrent", "dependency", "independent"]
        ):
            return PlanStrategy.dag_plan
        if intent.complexity == ComplexityLevel.simple:
            return PlanStrategy.direct
        return PlanStrategy.linear_plan

    def create_plan(
        self,
        intent: TaskIntent,
        candidates: list[CapabilityRoutingCard],
        strategy: PlanStrategy,
    ) -> TaskPlan:
        selected_ids = [candidate.id for candidate in candidates]
        plan_id = f"task-decomposition-plan:{hashlib.sha1(intent.raw_request.encode()).hexdigest()[:12]}"
        nodes = self._nodes_for_strategy(intent, candidates, strategy)
        return TaskPlan(
            plan_id=plan_id,
            goal=intent.goal,
            assumptions=intent.assumptions,
            non_goals=["Do not use unregistered capabilities.", "Do not store private reasoning in logs."],
            strategy=strategy,
            nodes=nodes,
            final_success_criteria=intent.success_criteria,
            max_iterations=3 if strategy in {PlanStrategy.react_loop, PlanStrategy.tree_search} else 1,
            budget=intent.budget,
        ).model_copy(
            update={
                "assumptions": [
                    *intent.assumptions,
                    f"Retrieved capability ids: {', '.join(selected_ids) if selected_ids else 'none'}.",
                ]
            }
        )

    def validate_plan(
        self,
        plan: TaskPlan,
        registry: CapabilityRegistry | None = None,
        context: PlanValidationContext | None = None,
    ) -> PlanValidationResult:
        return self.validator.validate(plan, registry or self.registry, context)

    def repair_plan(
        self,
        plan: TaskPlan,
        validation_errors: PlanValidationResult,
        registry: CapabilityRegistry | None = None,
        context: PlanValidationContext | None = None,
    ) -> TaskPlan:
        active_registry = registry or self.registry
        repaired_nodes: list[TaskNode] = []
        missing_codes = {
            "TASK_PLAN_CANDIDATE_CAPABILITY_MISSING",
            "TASK_PLAN_SELECTED_CAPABILITY_MISSING",
        }
        missing_node_ids = {
            issue.node_id for issue in validation_errors.issues if issue.reason_code in missing_codes and issue.node_id
        }
        approval_node_ids = {
            issue.node_id
            for issue in validation_errors.issues
            if issue.reason_code == "TASK_PLAN_RISK_APPROVAL_GATE_MISSING" and issue.node_id
        }
        for node in plan.nodes:
            update: dict[str, Any] = {}
            if node.id in missing_node_ids:
                update["candidate_capabilities"] = [
                    capability_id for capability_id in node.candidate_capabilities if active_registry.get(capability_id)
                ]
                if node.selected_capability and active_registry.get(node.selected_capability) is None:
                    update["selected_capability"] = None
            if node.id in approval_node_ids:
                update["requires_approval"] = True
            repaired_nodes.append(node.model_copy(update=update))
        return plan.model_copy(update={"nodes": repaired_nodes})

    def decompose(self, raw_request: str, context: dict[str, Any] | None = None) -> TaskPlan:
        intent = self.classify_intent(raw_request, context)
        candidates = self.retrieve_capabilities(intent)
        strategy = self.select_strategy(intent, candidates)
        return self.create_plan(intent, candidates, strategy)

    def _nodes_for_strategy(
        self,
        intent: TaskIntent,
        candidates: list[CapabilityRoutingCard],
        strategy: PlanStrategy,
    ) -> list[TaskNode]:
        if strategy == PlanStrategy.human_in_loop:
            return [
                TaskNode(
                    id="node:human-clarification",
                    title="Clarify Request",
                    objective="Collect the missing decision needed to proceed safely.",
                    decomposition_strategy=TaskNodeStrategy.human_approval,
                    candidate_capabilities=[],
                    input_bindings={"questions": intent.clarification_questions},
                    success_criteria=["Clarification is available before capability execution."],
                    risk_level=intent.risk_level,
                    requires_approval=True if intent.risk_level in {RiskLevel.high, RiskLevel.critical} else False,
                )
            ]

        top = candidates[0] if candidates else None
        second = candidates[1] if len(candidates) > 1 else None
        if strategy == PlanStrategy.dag_plan and second is not None:
            return [
                self._capability_node("node:branch-a", "Run First Independent Step", intent, top, TaskNodeStrategy.parallel_child),
                self._capability_node("node:branch-b", "Run Second Independent Step", intent, second, TaskNodeStrategy.parallel_child),
                TaskNode(
                    id="node:evaluate",
                    title="Evaluate Combined Result",
                    objective="Evaluate independent outputs against final success criteria.",
                    depends_on=["node:branch-a", "node:branch-b"],
                    decomposition_strategy=TaskNodeStrategy.evaluate,
                    input_bindings={"branch_a": "$node:branch-a", "branch_b": "$node:branch-b"},
                    success_criteria=intent.success_criteria,
                    risk_level=RiskLevel.low,
                ),
            ]

        if strategy == PlanStrategy.linear_plan and top is not None:
            return [
                self._capability_node("node:step-1", "Execute Primary Step", intent, top, TaskNodeStrategy.linear),
                TaskNode(
                    id="node:evaluate",
                    title="Evaluate Result",
                    objective="Evaluate the primary output against success criteria.",
                    depends_on=["node:step-1"],
                    decomposition_strategy=TaskNodeStrategy.evaluate,
                    input_bindings={"result": "$node:step-1"},
                    success_criteria=intent.success_criteria,
                    risk_level=RiskLevel.low,
                ),
            ]

        if strategy == PlanStrategy.react_loop and top is not None:
            node = self._capability_node("node:react", "Run Feedback-Oriented Step", intent, top, TaskNodeStrategy.react_loop)
            return [node.model_copy(update={"failure_modes": ["Tool feedback does not satisfy criteria."]})]

        if strategy == PlanStrategy.tree_search and top is not None:
            node = self._capability_node("node:tree-search", "Compare Candidate Path", intent, top, TaskNodeStrategy.linear)
            return [node.model_copy(update={"failure_modes": ["Ambiguity remains unresolved."]})]

        if strategy == PlanStrategy.skill_reuse and top is not None:
            return [self._capability_node("node:skill-reuse", "Reuse Known Workflow", intent, top, TaskNodeStrategy.direct)]

        if top is not None:
            return [self._capability_node("node:direct", "Execute Direct Task", intent, top, TaskNodeStrategy.direct)]

        return [
            TaskNode(
                id="node:no-capability",
                title="No Matching Capability",
                objective="Record that no registered capability matched the request.",
                decomposition_strategy=TaskNodeStrategy.evaluate,
                candidate_capabilities=[],
                input_bindings={"goal": intent.goal},
                success_criteria=["A safe no-capability result is recorded."],
                risk_level=RiskLevel.low,
            )
        ]

    def _capability_node(
        self,
        node_id: str,
        title: str,
        intent: TaskIntent,
        card: CapabilityRoutingCard,
        strategy: TaskNodeStrategy,
    ) -> TaskNode:
        return TaskNode(
            id=node_id,
            title=title,
            objective=intent.goal,
            decomposition_strategy=strategy,
            candidate_capabilities=[card.id],
            selected_capability=card.id,
            input_bindings={"request": intent.raw_request},
            expected_output_schema=None,
            success_criteria=intent.success_criteria,
            failure_modes=["Capability output does not satisfy success criteria."],
            risk_level=card.risk_level,
            requires_approval=card.requires_approval,
        )

    def _goal_summary(self, request: str) -> str:
        if not request:
            return "Clarify the requested task."
        first_line = request.splitlines()[0].strip()
        first_sentence = first_line.split(".", 1)[0].strip()
        return first_sentence[:240] or "Address the requested task."

    def _extract_constraints(self, request: str) -> list[str]:
        constraints: list[str] = []
        for line in request.splitlines():
            lowered = line.lower()
            if any(marker in lowered for marker in ["must", "do not", "don't", "only", "without", "keep", "before"]):
                constraints.append(line.strip("- ").strip())
        return list(dict.fromkeys(constraint for constraint in constraints if constraint))

    def _ambiguity_level(self, lowered_request: str) -> AmbiguityLevel:
        markers = ["maybe", "unclear", "ambiguous", "or something", "not sure", "?"]
        count = sum(1 for marker in markers if marker in lowered_request)
        if count >= 2:
            return AmbiguityLevel.high
        if count == 1:
            return AmbiguityLevel.medium
        return AmbiguityLevel.low

    def _complexity_level(self, lowered_request: str) -> ComplexityLevel:
        if any(marker in lowered_request for marker in ["roadmap", "long horizon", "multi-week", "multi month"]):
            return ComplexityLevel.long_horizon
        step_markers = sum(lowered_request.count(marker) for marker in [" and ", " then ", " after ", " before "])
        if step_markers >= 4 or len(lowered_request.split()) > 120:
            return ComplexityLevel.complex
        if step_markers >= 1 or len(lowered_request.split()) > 24:
            return ComplexityLevel.moderate
        return ComplexityLevel.simple

    def _risk_level(self, lowered_request: str) -> RiskLevel:
        if any(marker in lowered_request for marker in ["credential", "secret", "production", "payment", "spend"]):
            return RiskLevel.critical
        if any(marker in lowered_request for marker in ["delete", "write", "shell", "external api", "private data"]):
            return RiskLevel.high
        if any(marker in lowered_request for marker in ["modify", "network", "approval", "personal"]):
            return RiskLevel.medium
        return RiskLevel.low

    def _expected_output(self, lowered_request: str) -> str:
        if "test" in lowered_request:
            return "validated test result"
        if "plan" in lowered_request:
            return "task plan"
        if "summar" in lowered_request:
            return "summary"
        if "code" in lowered_request or "implement" in lowered_request:
            return "implemented change"
        return "completed task output"

    def _success_criteria(self, expected_output: str | None) -> list[str]:
        return [
            "Uses only registered capabilities.",
            f"Produces {expected_output or 'the expected output'}.",
            "Output satisfies declared constraints.",
        ]
