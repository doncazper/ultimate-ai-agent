#!/usr/bin/env python3
"""Verify honest capability-maturity evidence without auto-graduating scores."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from scripts.run_agent_capability_evaluation import (  # noqa: E402
    run_agent_capability_evaluation,
)
from ultimate_ai_agent.core.evals import (  # noqa: E402
    AgentCapabilityEvaluationReport,
    build_capability_maturity_read_model,
)


class CapabilityMaturityVerificationError(RuntimeError):
    pass


def verify_report(report: AgentCapabilityEvaluationReport) -> None:
    read_model = build_capability_maturity_read_model(report)
    if read_model.verification_posture != "automated_evidence_ready":
        raise CapabilityMaturityVerificationError(
            "one or more components lack complete bounded automated evidence"
        )
    if read_model.uplift_proven_count != 0:
        raise CapabilityMaturityVerificationError(
            "automated evidence must not graduate a score"
        )
    if read_model.automated_evidence_ready_count != 12:
        raise CapabilityMaturityVerificationError("automated evidence count drift")
    if read_model.manual_validation_required_count != 11:
        raise CapabilityMaturityVerificationError("manual validation count drift")
    if read_model.external_dependency_required_count != 1:
        raise CapabilityMaturityVerificationError("external dependency count drift")
    if read_model.ceiling_defended_count != 4:
        raise CapabilityMaturityVerificationError(
            "capability score ceiling count drift"
        )
    if read_model.verified_weighted_score != read_model.baseline_weighted_score:
        raise CapabilityMaturityVerificationError(
            "unaccepted scores must remain at the evidence-backed baseline"
        )
    if not all(item.next_acceptance_ref for item in read_model.components):
        raise CapabilityMaturityVerificationError("acceptance path is incomplete")
    if not read_model.content_free or read_model.raw_content_persisted:
        raise CapabilityMaturityVerificationError(
            "maturity evidence is not content-free"
        )
    if read_model.authority_granted:
        raise CapabilityMaturityVerificationError("maturity evidence granted authority")


def main() -> int:
    report = run_agent_capability_evaluation()
    verify_report(report)
    read_model = build_capability_maturity_read_model(report)
    print("Capability maturity evidence-readiness verification passed")
    print(f"Components: {read_model.component_count}")
    print(
        "Scores: "
        f"baseline={read_model.baseline_weighted_score} "
        f"verified={read_model.verified_weighted_score}"
    )
    print(
        "Evidence: "
        f"automated_ready={read_model.automated_evidence_ready_count} "
        f"manual_required={read_model.manual_validation_required_count} "
        f"external_required={read_model.external_dependency_required_count} "
        f"graduated={read_model.uplift_proven_count}"
    )
    print("Authority granted: no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["CapabilityMaturityVerificationError", "main", "verify_report"]
