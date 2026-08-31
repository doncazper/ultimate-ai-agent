# ruff: noqa: F401,F403,F405
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

from ultimate_ai_agent.core.gate.criteria import (
    FoundationGateCriterion,
    default_foundation_gate_criteria,
)
from ultimate_ai_agent.core.gate.evaluation_context import GateEvaluationContext
from ultimate_ai_agent.core.gate.legacy_checks import *  # noqa: F401,F403
from ultimate_ai_agent.core.gate.legacy_checks import (
    FoundationGateLegacyChecksMixin,
    _is_static_safety_scan_allowed_file,
)
from ultimate_ai_agent.core.gate.reports import (
    FoundationGateReport,
    FoundationGateResult,
    build_foundation_gate_report,
)


class FoundationGateEvaluator(FoundationGateLegacyChecksMixin):
    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = root or Path(__file__).resolve().parents[4]
        self.src_root = self.root / "src" / "ultimate_ai_agent"
        self._context = GateEvaluationContext(self.root)

    def evaluate(
        self,
        criteria: Optional[List[FoundationGateCriterion]] = None,
    ) -> FoundationGateReport:
        self._context = GateEvaluationContext(self.root)
        selected_criteria = criteria or default_foundation_gate_criteria()
        evaluator_map = self._evaluator_map(selected_criteria)
        results = [
            evaluator_map.get(criterion.criterion_id, self._skipped)(criterion)
            for criterion in selected_criteria
        ]
        version = self._active_version() or "unknown"
        return build_foundation_gate_report(
            version=version,
            results=results,
            trace_id="trace_foundation_gate",
        )

    def _evaluator_map(
        self, criteria: Iterable[FoundationGateCriterion]
    ) -> Dict[str, Callable[[FoundationGateCriterion], FoundationGateResult]]:
        evaluator_map: Dict[
            str, Callable[[FoundationGateCriterion], FoundationGateResult]
        ] = {}
        for criterion in criteria:
            method_name = f"check_{criterion.criterion_id}"
            evaluator = getattr(self, method_name, None)
            if callable(evaluator):
                evaluator_map[criterion.criterion_id] = evaluator
        return evaluator_map
