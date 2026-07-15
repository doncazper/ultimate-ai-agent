#!/usr/bin/env python3
"""Verify honest capability-maturity evidence without auto-graduating scores."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from scripts.run_agent_capability_evaluation import (  # noqa: E402
    run_agent_capability_evaluation,
)
from ultimate_ai_agent.core.evals import (  # noqa: E402
    CAPABILITY_COMPONENT_IDS,
    CAPABILITY_MATURITY_BASELINE_FINGERPRINT_REF,
    CAPABILITY_MATURITY_BASELINE_SCORES,
    CAPABILITY_MATURITY_BASELINE_SOURCE_REF,
    AgentCapabilityEvaluationReport,
    CapabilityMaturityGateKind,
    CapabilityMaturityGateStatus,
    build_capability_maturity_read_model,
)


class CapabilityMaturityVerificationError(RuntimeError):
    pass


BASELINE_ARTIFACT = (
    ROOT
    / "docs"
    / "benchmarks"
    / "runtime_capability_foundation"
    / "goat_comparison_20260712.json"
)


def _verify_canonical_baseline() -> None:
    if BASELINE_ARTIFACT.is_symlink() or not BASELINE_ARTIFACT.is_file():
        raise CapabilityMaturityVerificationError(
            "canonical baseline must be a regular repository file"
        )
    try:
        payload = json.loads(BASELINE_ARTIFACT.read_text(encoding="utf-8"))
        rows = payload["initial_scores"]["uaa"]["components"]
        findings = payload["findings"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise CapabilityMaturityVerificationError(
            "canonical baseline artifact shape drift"
        ) from exc
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise CapabilityMaturityVerificationError("canonical baseline rows drift")
    observed = {str(row.get("component_id")): row.get("score") for row in rows}
    if (
        tuple(row.get("component_id") for row in rows)
        != tuple(CAPABILITY_COMPONENT_IDS)
        or observed != CAPABILITY_MATURITY_BASELINE_SCORES
    ):
        raise CapabilityMaturityVerificationError(
            "runtime baseline drifted from canonical comparison scores"
        )
    finding_weights = {
        str(row.get("component")): row.get("weight")
        for row in findings
        if isinstance(row, dict)
    }
    definition_weights = {
        item.component_id: item.weight
        for item in build_capability_maturity_read_model().components
    }
    if finding_weights != definition_weights:
        raise CapabilityMaturityVerificationError(
            "runtime weights drifted from canonical comparison weights"
        )


def verify_report(report: AgentCapabilityEvaluationReport) -> None:
    _verify_canonical_baseline()
    read_model = build_capability_maturity_read_model(report)
    if read_model.verification_posture != "automated_evidence_ready":
        raise CapabilityMaturityVerificationError(
            "one or more components lack bounded automated-test evidence"
        )
    if read_model.uplift_proven_count != 0:
        raise CapabilityMaturityVerificationError(
            "automated evidence must not graduate a score"
        )
    if read_model.automated_evidence_ready_count != read_model.component_count:
        raise CapabilityMaturityVerificationError("automated-test evidence count drift")
    if read_model.manual_validation_required_count != 0:
        raise CapabilityMaturityVerificationError(
            "components cannot skip unresolved runtime or operator gates"
        )
    if read_model.external_dependency_required_count != 1:
        raise CapabilityMaturityVerificationError("external dependency count drift")
    if read_model.ceiling_defended_count != 0:
        raise CapabilityMaturityVerificationError(
            "automated tests alone cannot defend a maturity ceiling"
        )
    if read_model.verified_weighted_score != read_model.baseline_weighted_score:
        raise CapabilityMaturityVerificationError(
            "unaccepted scores must remain at the evidence-backed baseline"
        )
    if not all(item.next_acceptance_ref for item in read_model.components):
        raise CapabilityMaturityVerificationError("acceptance path is incomplete")
    if read_model.baseline_source_ref != CAPABILITY_MATURITY_BASELINE_SOURCE_REF:
        raise CapabilityMaturityVerificationError("baseline source ref drift")
    if (
        read_model.baseline_source_fingerprint_ref
        != CAPABILITY_MATURITY_BASELINE_FINGERPRINT_REF
    ):
        raise CapabilityMaturityVerificationError("baseline fingerprint drift")
    for component in read_model.components:
        gates = {gate.gate_kind: gate for gate in component.gates}
        if gates[CapabilityMaturityGateKind.automated_tests].status != (
            CapabilityMaturityGateStatus.satisfied
        ):
            raise CapabilityMaturityVerificationError(
                "automated-test gate did not preserve verifier truth"
            )
        for gate_kind in (
            CapabilityMaturityGateKind.runtime_scenario,
            CapabilityMaturityGateKind.operator_surface,
            CapabilityMaturityGateKind.recovery_and_failure,
            CapabilityMaturityGateKind.independent_acceptance,
        ):
            if gates[gate_kind].status == CapabilityMaturityGateStatus.satisfied:
                raise CapabilityMaturityVerificationError(
                    "command results silently satisfied an independent evidence gate"
                )
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
    print("Capability maturity gate-specific evidence verification passed")
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
