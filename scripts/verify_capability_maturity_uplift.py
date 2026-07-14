#!/usr/bin/env python3
"""Verify the bounded 16-component capability maturity uplift evidence."""

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
    if read_model.verification_posture != "targets_proven":
        raise CapabilityMaturityVerificationError(
            "one or more capability maturity targets lack complete evidence"
        )
    if read_model.uplift_proven_count != read_model.uplift_target_count:
        raise CapabilityMaturityVerificationError("bounded uplift count drift")
    if read_model.uplift_proven_count != 12 or read_model.ceiling_defended_count != 4:
        raise CapabilityMaturityVerificationError("capability score ceiling count drift")
    if read_model.verified_weighted_score != read_model.target_weighted_score:
        raise CapabilityMaturityVerificationError("verified score did not reach target")
    if not read_model.content_free or read_model.raw_content_persisted:
        raise CapabilityMaturityVerificationError("maturity evidence is not content-free")
    if read_model.authority_granted:
        raise CapabilityMaturityVerificationError("maturity evidence granted authority")


def main() -> int:
    report = run_agent_capability_evaluation()
    verify_report(report)
    read_model = build_capability_maturity_read_model(report)
    print("Capability maturity uplift verification passed")
    print(f"Components: {read_model.component_count}")
    print(
        "Scores: "
        f"baseline={read_model.baseline_weighted_score} "
        f"verified={read_model.verified_weighted_score}"
    )
    print(
        "Evidence: "
        f"uplifts={read_model.uplift_proven_count} "
        f"ceilings={read_model.ceiling_defended_count}"
    )
    print("Authority granted: no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["CapabilityMaturityVerificationError", "main", "verify_report"]
