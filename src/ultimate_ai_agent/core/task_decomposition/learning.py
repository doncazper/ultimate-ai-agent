from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import Iterable

from ultimate_ai_agent.core.task_decomposition.contracts import (
    DAGExecutionResult,
    DAGExecutionStatus,
    NodeExecutionStatus,
    PromotionCandidate,
    ReflectionRecord,
    TaskPlan,
)


PromotionHook = Callable[[PromotionCandidate], None]


class ReflectionStore:
    def __init__(self, promotion_hook: PromotionHook | None = None, promotion_threshold: int = 3):
        self._reflections: list[ReflectionRecord] = []
        self._promotion_candidates: dict[str, PromotionCandidate] = {}
        self.promotion_hook = promotion_hook
        self.promotion_threshold = promotion_threshold

    def record_execution(self, plan: TaskPlan, result: DAGExecutionResult) -> list[ReflectionRecord]:
        created: list[ReflectionRecord] = []
        for record in result.node_records:
            if record.status in {NodeExecutionStatus.failed, NodeExecutionStatus.skipped, NodeExecutionStatus.awaiting_approval}:
                created.append(
                    self.record_reflection(
                        plan_id=plan.plan_id,
                        node_id=record.node_id,
                        capability_id=record.selected_capability,
                        safe_summary=record.safe_summary,
                        reason_codes=record.reason_codes,
                    )
                )
        if result.status == DAGExecutionStatus.succeeded:
            self.record_successful_fragment(plan)
        return created

    def record_reflection(
        self,
        *,
        plan_id: str,
        safe_summary: str,
        node_id: str | None = None,
        capability_id: str | None = None,
        reason_codes: list[str] | None = None,
    ) -> ReflectionRecord:
        suffix = hashlib.sha1(f"{plan_id}:{node_id}:{capability_id}:{len(self._reflections)}".encode()).hexdigest()[:12]
        record = ReflectionRecord(
            reflection_id=f"task-reflection:{suffix}",
            plan_id=plan_id,
            node_id=node_id,
            capability_id=capability_id,
            safe_summary=safe_summary,
            reason_codes=reason_codes or [],
        )
        self._reflections.append(record)
        return record

    def record_successful_fragment(self, plan: TaskPlan) -> PromotionCandidate:
        capability_ids = [
            node.selected_capability
            for node in sorted(plan.nodes, key=lambda item: item.id)
            if node.selected_capability
        ]
        fragment_key = self._fragment_key(plan.strategy.value, capability_ids)
        candidate = self._promotion_candidates.get(fragment_key)
        if candidate is None:
            candidate = PromotionCandidate(
                candidate_id=f"task-promotion:{fragment_key[:12]}",
                fragment_key=fragment_key,
                plan_ids=[],
                capability_ids=list(dict.fromkeys(capability_ids)),
                success_count=0,
                safe_summary="Repeated successful task-plan fragment candidate.",
            )
        candidate = candidate.model_copy(
            update={
                "plan_ids": list(dict.fromkeys([*candidate.plan_ids, plan.plan_id])),
                "success_count": candidate.success_count + 1,
            }
        )
        if (
            not candidate.promoted
            and candidate.success_count >= self.promotion_threshold
            and self.promotion_hook is not None
        ):
            self.promotion_hook(candidate)
            candidate = candidate.model_copy(update={"promoted": True})
        self._promotion_candidates[fragment_key] = candidate
        return candidate

    def reflections(self) -> list[ReflectionRecord]:
        return list(self._reflections)

    def promotion_candidates(self) -> list[PromotionCandidate]:
        return list(self._promotion_candidates.values())

    def _fragment_key(self, strategy: str, capability_ids: Iterable[str]) -> str:
        body = "|".join([strategy, *capability_ids])
        return hashlib.sha1(body.encode()).hexdigest()
