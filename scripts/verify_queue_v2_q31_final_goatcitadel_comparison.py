#!/usr/bin/env python3
"""Verify the finite, redacted Queue V2 Q31 comparison packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT = (
    ROOT / "docs" / "benchmarks" / "q31_goat_maturity_input_20260906.json"
)
DEFAULT_REPORT = (
    ROOT / "docs" / "benchmarks" / "Q31_FINAL_GOATCITADEL_COMPARISON_20260906.md"
)
SCHEMA_VERSION = "goat-comparison-maturity.v2"
BASELINES = {
    "uaa": "git-sha:817d84d8f0e4660de5dfcff9cb215e5330d8714c",
    "goatcitadel": "git-sha:41d0f2e52910c60c39fa0b788042638eddf302e5",
}
WEIGHTS = {
    "reasoning": 8,
    "planning": 8,
    "learning": 8,
    "memory": 9,
    "communication": 7,
    "action": 9,
    "authority": 10,
    "code": 6,
    "research": 5,
    "providers": 6,
    "evidence": 9,
    "safety": 10,
    "ux": 7,
    "cli_api": 6,
    "extensibility": 6,
    "product_loop": 10,
}
GATE_MAXIMA = {
    "contract": 1,
    "implementation": 2,
    "tests": 1,
    "runtime_integration": 2,
    "operator_surface": 1,
    "reference_scenario": 1,
    "failure_recovery_audit": 1,
    "independent_validation": 1,
}
STATUSES = {
    "implemented",
    "partial",
    "planned",
    "mock-only",
    "blocked",
    "deprecated",
    "contradicted",
    "unknown",
}
VALIDATION_POSTURES = {
    "accepted",
    "automated_evidence_ready",
    "manual_validation_required",
    "external_dependency_required",
    "not_evaluated",
}
REQUIRED_REPORT_SECTIONS = (
    "## Scope and exact baselines",
    "## Executive profile",
    "## Gate scorecard",
    "## Component analysis",
    "## Direct product observation",
    "## Feature parity matrix",
    "## Strengths, weaknesses, and missing capabilities",
    "## Reciprocal learning",
    "## Recommendations and owners",
    "## Bounded 30-day plan",
    "## Final verdict",
)
PROHIBITED_TEXT = (
    "/Users/",
    "/private/tmp/",
    "file://",
    "sess_",
    "api_key=",
    "password=",
)
UAA_REF = re.compile(r"^repo-ref:uaa@[0-9a-f]{8}:([^#]+)$")
GOAT_REF = re.compile(r"^repo-ref:goat@[0-9a-f]{8}:([^#]+)$")


class VerificationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def _safe_refs(component: dict[str, Any], field: str, *, required: bool = False) -> list[str]:
    value = component.get(field, [])
    _require(
        isinstance(value, list)
        and all(isinstance(item, str) and item.strip() for item in value),
        f"{field} must contain safe string refs",
    )
    if required:
        _require(bool(value), f"{field} cannot be empty")
    return value


def _component_score(component: dict[str, Any]) -> int:
    gates = component["gates"]
    raw_score = sum(gates.values())
    ceilings: list[int] = []
    status = component["status"]
    if status in {"planned", "mock-only", "deprecated", "unknown"}:
        ceilings.append(2)
    elif status == "contradicted":
        ceilings.append(3)
    elif status == "blocked":
        ceilings.append(4)
    elif status == "partial":
        ceilings.append(6)
    if gates["implementation"] == 0:
        ceilings.append(2)
    elif gates["implementation"] == 1:
        ceilings.append(6)
    if gates["tests"] == 0:
        ceilings.append(5)
    if gates["runtime_integration"] == 0:
        ceilings.append(4)
    elif gates["runtime_integration"] == 1:
        ceilings.append(7)
    if component["operator_facing"] and gates["operator_surface"] == 0:
        ceilings.append(7)
    if gates["reference_scenario"] == 0:
        ceilings.append(8)
    if gates["failure_recovery_audit"] == 0:
        ceilings.append(8)
    if gates["independent_validation"] == 0:
        ceilings.append(8)
    if component["validation_posture"] != "accepted":
        ceilings.append(8)
    if (
        component.get("representative_scope_count", 0) < 2
        or not component.get("breadth_evidence_refs")
        or not component.get("repeatability_evidence_refs")
    ):
        ceilings.append(9)
    if component.get("prior_verified_score") is not None and component["validation_posture"] != "accepted":
        ceilings.append(component["prior_verified_score"])
    if component.get("contradiction_refs"):
        ceilings.append(6)
    if component.get("critical_failure_refs"):
        ceilings.append(3)
    return min(raw_score, min(ceilings, default=10))


def _band(score: int) -> str:
    if score <= 19:
        return "Minimal evidence"
    if score <= 39:
        return "Claimed or mocked foundation"
    if score <= 54:
        return "Partial system"
    if score <= 69:
        return "Usable system"
    if score <= 84:
        return "Strong system"
    if score <= 94:
        return "Mature system"
    return "Exceptional evidence"


def _walk_for_unsafe_text(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", key.lower())
            _require(
                normalized not in {"rawprompt", "rawresponse", "providerpayload", "rawlog", "localpath"},
                f"unsafe durable field: {key}",
            )
            _walk_for_unsafe_text(child)
    elif isinstance(value, list):
        for child in value:
            _walk_for_unsafe_text(child)
    elif isinstance(value, str):
        _require(not any(fragment in value for fragment in PROHIBITED_TEXT), "unsafe durable text")
        _require(re.search(r"\bsk-[A-Za-z0-9]{8,}", value) is None, "unsafe durable text")


def verify_data(data: dict[str, Any], report: str) -> dict[str, Any]:
    _require(data.get("schema_version") == SCHEMA_VERSION, "schema version drift")
    _require(data.get("comparison_date") == "2026-09-06", "comparison date drift")
    _require(data.get("baselines", {}).get("uaa", {}).get("commit_ref") == BASELINES["uaa"], "UAA baseline drift")
    _require(
        data.get("baselines", {}).get("goatcitadel", {}).get("commit_ref") == BASELINES["goatcitadel"],
        "GoatCitadel baseline drift",
    )
    authority = data.get("authority_granted")
    _require(isinstance(authority, dict) and authority and not any(authority.values()), "comparison cannot grant authority")
    method = data.get("method", {})
    _require(method.get("controlled_model_task_trials") == "not_measured", "controlled task posture drift")
    _require(method.get("product_experience") == "single_evaluator_formative_only", "product experience posture drift")
    _require(method.get("raw_model_intelligence_scored") is False, "raw model intelligence cannot be scored")

    systems = data.get("systems")
    _require(isinstance(systems, dict) and set(systems) == set(BASELINES), "system inventory drift")
    expected = data.get("expected_scores", {}).get("systems")
    _require(isinstance(expected, dict) and set(expected) == set(BASELINES), "expected score inventory drift")
    for system_name, components in systems.items():
        _require(isinstance(components, dict) and set(components) == set(WEIGHTS), f"{system_name}: component inventory drift")
        weighted_points = 0
        for component_name, component in components.items():
            _require(isinstance(component, dict), f"{system_name}/{component_name}: invalid component")
            _require(component.get("weight") == WEIGHTS[component_name], f"{system_name}/{component_name}: weight drift")
            _require(component.get("status") in STATUSES, f"{system_name}/{component_name}: invalid status")
            _require(component.get("validation_posture") in VALIDATION_POSTURES, f"{system_name}/{component_name}: invalid validation posture")
            _require(isinstance(component.get("operator_facing"), bool), f"{system_name}/{component_name}: operator flag drift")
            gates = component.get("gates")
            _require(isinstance(gates, dict) and set(gates) == set(GATE_MAXIMA), f"{system_name}/{component_name}: gate inventory drift")
            for gate_name, maximum in GATE_MAXIMA.items():
                gate = gates[gate_name]
                _require(type(gate) is int and 0 <= gate <= maximum, f"{system_name}/{component_name}/{gate_name}: invalid gate")
            _require(gates["independent_validation"] == 0, f"{system_name}/{component_name}: independent validation not available")
            _require(component["validation_posture"] != "accepted", f"{system_name}/{component_name}: self-evidence cannot be accepted")
            _require(not _safe_refs(component, "acceptance_evidence_refs"), f"{system_name}/{component_name}: acceptance refs not authorized")
            refs = _safe_refs(component, "evidence_refs", required=True)
            for field in ("breadth_evidence_refs", "repeatability_evidence_refs", "contradiction_refs", "critical_failure_refs", "blocker_refs"):
                _safe_refs(component, field)
            for ref in refs:
                match = UAA_REF.match(ref)
                if match:
                    _require((ROOT / match.group(1)).is_file(), f"missing UAA evidence file: {match.group(1)}")
                elif ref.startswith("repo-ref:goat@"):
                    _require(GOAT_REF.match(ref) is not None, "invalid GoatCitadel repo ref")
            score = _component_score(component)
            _require(expected[system_name]["components"].get(component_name) == score, f"{system_name}/{component_name}: expected score drift")
            weighted_points += score * WEIGHTS[component_name]
        raw_total = round(weighted_points / sum(WEIGHTS.values()) * 10, 4)
        reported = int(raw_total + 0.5)
        _require(expected[system_name].get("weighted_total_raw") == raw_total, f"{system_name}: raw weighted total drift")
        _require(expected[system_name].get("weighted_total_reported") == reported, f"{system_name}: reported weighted total drift")
        _require(expected[system_name].get("band") == _band(reported), f"{system_name}: maturity band drift")

    observations = data.get("direct_observations")
    _require(isinstance(observations, list) and len(observations) >= 6, "direct observation inventory incomplete")
    _require({item.get("system") for item in observations} == set(BASELINES), "both systems require direct observation")
    _require(any(item.get("scenario_ref") == "scenario-ref:q31:responsive-390x844" and item.get("system") == "uaa" for item in observations), "UAA mobile observation missing")
    _require(any(item.get("scenario_ref") == "scenario-ref:q31:responsive-390x844" and item.get("system") == "goatcitadel" for item in observations), "GoatCitadel mobile observation missing")

    routes = data.get("residual_gap_routes")
    _require(isinstance(routes, list) and routes, "residual gap routes missing")
    owners = {item.get("owner") for item in routes}
    _require({"Q32", "Q33", "Q36"}.issubset(owners), "required queue owner routing missing")
    learning = data.get("reciprocal_learning")
    _require(isinstance(learning, list) and len(learning) >= 6, "reciprocal learning ledger incomplete")
    _require({item.get("direction") for item in learning} == {"goatcitadel_to_uaa", "uaa_to_goatcitadel"}, "reciprocal direction missing")
    _require(all(item.get("disposition") in {"adapt", "study_only", "do_not_borrow"} for item in learning), "invalid transfer disposition")

    _walk_for_unsafe_text(data)
    for section in REQUIRED_REPORT_SECTIONS:
        _require(section in report, f"report section missing: {section}")
    _require("not a controlled" in report.lower(), "report must preserve non-empirical posture")
    _require("73" in report and "70" in report, "report score binding missing")
    _require("Q32" in report and "Q33" in report and "Q36" in report, "report owner routing missing")
    _require(not any(fragment in report for fragment in PROHIBITED_TEXT), "unsafe report text")
    _require(re.search(r"\bsk-[A-Za-z0-9]{8,}", report) is None, "unsafe report text")
    return data


def verify(artifact: Path = DEFAULT_ARTIFACT, report_path: Path = DEFAULT_REPORT) -> dict[str, Any]:
    _require(artifact.resolve() == DEFAULT_ARTIFACT.resolve(), "artifact path is not canonical")
    _require(report_path.resolve() == DEFAULT_REPORT.resolve(), "report path is not canonical")
    _require(artifact.stat().st_size <= 250_000, "comparison artifact is unbounded")
    _require(report_path.stat().st_size <= 150_000, "comparison report is unbounded")
    data = json.loads(artifact.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    return verify_data(data, report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    data = verify(args.artifact, args.report)
    scores = data["expected_scores"]["systems"]
    print(
        json.dumps(
            {
                "status": "verified",
                "comparison_ref": data["comparison_ref"],
                "uaa": scores["uaa"]["weighted_total_reported"],
                "goatcitadel": scores["goatcitadel"]["weighted_total_reported"],
                "controlled_task_performance": "not_measured",
                "authority_granted": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
