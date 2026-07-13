#!/usr/bin/env python3
"""Verify the bounded, redacted UAA-GoatCitadel comparison artifact."""

from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from ultimate_ai_agent.core.execution.validation import (  # noqa: E402
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.safe_contract_text import (  # noqa: E402
    validate_safe_contract_text_shape,
)
from ultimate_ai_agent.core.model_runtime.redaction import (  # noqa: E402
    contains_secret_like,
)
from ultimate_ai_agent.core.secrets.redaction import (  # noqa: E402
    contains_obvious_secret,
)
from scripts.run_agent_capability_evaluation import (  # noqa: E402
    ADDITIONAL_SCENARIOS,
    PHASE09_SCENARIOS,
    _scenario_fingerprint,
    evaluation_registry_fingerprint,
)
from scripts.run_uaa_runtime_phase09_benchmark import (  # noqa: E402
    scenario_execution_fingerprint,
)


DEFAULT_ARTIFACT = (
    ROOT
    / "docs"
    / "benchmarks"
    / "runtime_capability_foundation"
    / "goat_comparison_20260712.json"
)
COMPONENT_IDS = (
    "reasoning_task_understanding",
    "planning_orchestration",
    "learning_adaptation",
    "memory_context_management",
    "communication_interaction",
    "action_tool_calling",
    "autonomy_authority",
    "code_implementation_assistance",
    "research_web_external",
    "model_provider_management",
    "evidence_audit_observability",
    "safety_security_failure",
    "ux_ai_cockpit",
    "cli_api_parity",
    "extensibility_ecosystem",
    "productized_agent_loop",
)
GATE_MAXIMA = {
    "contract": 1,
    "implementation": 2,
    "tests": 2,
    "runtime_integration": 2,
    "operator_surface": 1,
    "reference_scenario": 1,
    "failure_recovery_audit": 1,
}
EVIDENCE_RE = re.compile(
    r"^repo-ref:(uaa|goatcitadel):([^#]+)#L([1-9][0-9]*)(?:-L([1-9][0-9]*))?$"
)
PROHIBITED_NORMALIZED_KEYS = {
    "rawprompt",
    "prompttext",
    "rawresponse",
    "providerpayload",
    "secretvalue",
    "credential",
    "localpath",
    "hostname",
    "username",
    "messagebody",
    "pagecontent",
    "rawlog",
}
SENSITIVE_KEY_FAMILIES = (
    "apikey",
    "authtoken",
    "accesstoken",
    "token",
    "privatekey",
    "password",
    "secret",
    "credential",
)
SAFE_SENSITIVE_KEY_SUFFIXES = (
    "ref",
    "refs",
    "hash",
    "hashes",
    "fingerprint",
    "posture",
    "status",
    "count",
    "counts",
    "enabled",
    "required",
)
UNSAFE_TEXT = ("/Users/", "/home/", "C:\\", "api_key=", "password=")
MAX_ARTIFACT_BYTES = 1_000_000
MAX_EVIDENCE_BYTES = 5_000_000


class VerificationError(ValueError):
    pass


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _walk(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized_key = _normalize_key(key)
            sensitive_family = any(
                family in normalized_key for family in SENSITIVE_KEY_FAMILIES
            )
            safe_suffix = normalized_key.endswith(SAFE_SENSITIVE_KEY_SUFFIXES)
            if normalized_key in PROHIBITED_NORMALIZED_KEYS or (
                sensitive_family and not safe_suffix
            ):
                raise VerificationError(f"unsafe durable field: {key}")
            _walk(nested)
    elif isinstance(value, list):
        for nested in value:
            _walk(nested)
    elif isinstance(value, str) and any(fragment in value for fragment in UNSAFE_TEXT):
        raise VerificationError("unsafe local or secret-like text")


def _safe_read(path: Path, *, root: Path, maximum_bytes: int) -> bytes:
    resolved_root = root.resolve(strict=True)
    try:
        relative = path.relative_to(root) if path.is_absolute() else path
    except ValueError as exc:
        raise VerificationError("unsafe comparison path") from exc
    if relative.is_absolute() or ".." in relative.parts:
        raise VerificationError("unsafe comparison path")
    current = root
    for part in relative.parts[:-1]:
        current = current / part
        current_stat = os.lstat(current)
        if stat.S_ISLNK(current_stat.st_mode) or not stat.S_ISDIR(current_stat.st_mode):
            raise VerificationError("comparison path parent must be a real directory")
    candidate = root / relative
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(candidate, flags)
    try:
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_nlink != 1:
            raise VerificationError("comparison input must be a single-link regular file")
        if file_stat.st_size > maximum_bytes:
            raise VerificationError("comparison input exceeds its size bound")
        resolved_candidate = candidate.resolve(strict=True)
        if not resolved_candidate.is_relative_to(resolved_root):
            raise VerificationError("comparison path escapes repository root")
        chunks: list[bytes] = []
        remaining = file_stat.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 64 * 1024))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) != file_stat.st_size:
            raise VerificationError("comparison input changed or exceeded its size bound")
        return payload
    finally:
        os.close(descriptor)


def _score(gates: dict[str, Any]) -> int:
    if set(gates) != set(GATE_MAXIMA):
        raise VerificationError("evidence gates drift")
    score = 0
    for name, maximum in GATE_MAXIMA.items():
        value = gates[name]
        if not isinstance(value, int) or not 0 <= value <= maximum:
            raise VerificationError(f"invalid evidence gate: {name}")
        score += value
    return score


def _weighted_total(findings: list[dict[str, Any]], system: str) -> float:
    numerator = sum(_score(item[f"{system}_gates"]) * item["weight"] for item in findings)
    return round(numerator / 124 * 10, 4)


def _goat_root() -> Path:
    configured = os.environ.get("UAA_GOAT_BENCHMARK_ROOT")
    return (
        Path(configured)
        if configured
        else Path.home() / "Documents" / "GitHub" / "GoatCitadel"
    )


def _validate_evidence_ref(value: str, system: str) -> None:
    match = EVIDENCE_RE.fullmatch(value)
    if match is None or match.group(1) != system:
        raise VerificationError(f"invalid comparison evidence ref: {value}")
    relative = Path(match.group(2))
    if relative.is_absolute() or ".." in relative.parts:
        raise VerificationError("comparison evidence path is unsafe")
    repo_root = ROOT if system == "uaa" else _goat_root()
    try:
        payload = _safe_read(relative, root=repo_root, maximum_bytes=MAX_EVIDENCE_BYTES)
    except FileNotFoundError as exc:
        label = "UAA" if system == "uaa" else "GoatCitadel"
        raise VerificationError(f"missing {label} comparison evidence") from exc
    line_count = payload.count(b"\n") + (0 if payload.endswith(b"\n") else 1)
    start = int(match.group(3))
    end = int(match.group(4) or match.group(3))
    if end < start or start > line_count or end > line_count:
        raise VerificationError("comparison evidence line range is invalid")


def _expected_report_projection() -> dict[str, Any]:
    observations = [
        {
            "scenario_ref": spec.scenario_id,
            "component_id": spec.component_id,
            "expected_status": spec.expected_status,
            "observed_status": spec.expected_status,
            "execution_fingerprint_ref": scenario_execution_fingerprint(spec),
            "failure_code": "none",
        }
        for spec in PHASE09_SCENARIOS
    ]
    observations.extend(
        {
            "scenario_ref": spec.scenario_ref,
            "component_id": spec.component_id,
            "expected_status": "passed",
            "observed_status": "passed",
            "execution_fingerprint_ref": _scenario_fingerprint(spec),
            "failure_code": "none",
        }
        for spec in ADDITIONAL_SCENARIOS
    )
    return {
        "schema_version": "uaa-agent-capability-evaluation.v1",
        "contract_ref": "contract-ref:agent-capability-evaluation:v1",
        "report_ref": "evaluation-report:uaa-agent-capability:20260712",
        "benchmark_ref": "benchmark-ref:uaa-goat-comparison:20260712",
        "registry_fingerprint_ref": evaluation_registry_fingerprint(),
        "status": "passed",
        "scenario_count": 21,
        "component_ids": list(COMPONENT_IDS),
        "safe_outcome_adherence_rate": 1.0,
        "verification_pass_rate": 1.0,
        "passed_unblocked_verifier_rate": round(20 / 21, 4),
        "passed_unblocked_verifier_count": 20,
        "task_completion_rate": None,
        "task_completion_count": None,
        "task_completion_posture": "not_measured",
        "blocked_safe_outcome_count": 1,
        "correctness_rate": None,
        "recovery_success_rate": None,
        "evidence_completeness_rate": None,
        "replay_correctness_rate": None,
        "operator_intervention_count": None,
        "false_completion_count": None,
        "unsupported_claim_count": None,
        "authority_policy_violation_count": None,
        "observations": observations,
        "content_free": True,
        "authority_granted": False,
    }


def _projection_digest(projection: dict[str, Any]) -> str:
    encoded = json.dumps(projection, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def verify_data(data: dict[str, Any]) -> dict[str, Any]:
    _walk(data)
    if contains_secret_like(data) or contains_obvious_secret(data):
        raise VerificationError("comparison contains secret-like material")
    if data.get("schema_version") != "uaa_goat_comparison_findings.v1":
        raise VerificationError("comparison schema drift")
    if data.get("authority_granted") is not False:
        raise VerificationError("comparison cannot grant authority")
    findings = data.get("findings")
    if not isinstance(findings, list) or tuple(
        item.get("component") for item in findings
    ) != COMPONENT_IDS:
        raise VerificationError("comparison requires the exact 16-component taxonomy")
    if sum(item.get("weight", 0) for item in findings) != 124:
        raise VerificationError("comparison weights must total 124")
    for item in findings:
        for system in ("uaa", "goatcitadel"):
            _score(item[f"{system}_gates"])
        refs = item.get("evidence_refs", {})
        for system in ("uaa", "goatcitadel"):
            values = refs.get(system)
            if not isinstance(values, list) or not values:
                raise VerificationError("every comparison component requires evidence refs")
            for value in values:
                _validate_evidence_ref(value, system)
        for required in (
            "missing_runtime_behavior",
            "authority_safety_risk",
            "operator_impact",
            "proposed_uaa_native_implementation",
            "acceptance_test_refs",
            "priority",
            "effort",
            "blocked_external_status",
        ):
            if not item.get(required):
                raise VerificationError(f"comparison finding missing {required}")
        for field in (
            "missing_runtime_behavior",
            "authority_safety_risk",
            "operator_impact",
            "proposed_uaa_native_implementation",
        ):
            validate_safe_execution_text(item[field], field)
            validate_safe_contract_text_shape(item[field], field)

    initial = data.get("initial_scores", {})
    expected_initial = {
        "uaa": _weighted_total(findings, "uaa"),
        "goatcitadel": _weighted_total(findings, "goatcitadel"),
    }
    for system, expected in expected_initial.items():
        if initial.get(system, {}).get("weighted_total_raw") != expected:
            raise VerificationError(f"{system} initial weighted total drift")
        if initial.get(system, {}).get("weighted_total_reported") != round(expected):
            raise VerificationError(f"{system} reported weighted total drift")
        component_scores = {
            item["component_id"]: item["score"]
            for item in initial.get(system, {}).get("components", [])
        }
        expected_scores = {
            item["component"]: _score(item[f"{system}_gates"])
            for item in findings
        }
        if component_scores != expected_scores:
            raise VerificationError(f"{system} initial component score drift")
    if data.get("final_scores") != initial:
        raise VerificationError("final scores changed without new bound evidence gates")

    result = data.get("implementation_result", {})
    if result.get("scenario_count") != 21 or result.get("component_count") != 16:
        raise VerificationError("capability evaluation coverage drift")
    if result.get("safe_outcome_adherence_rate") != 1:
        raise VerificationError("safe-outcome adherence drift")
    if result.get("verification_pass_rate") != 1:
        raise VerificationError("scenario verifier pass-rate drift")
    if result.get("passed_unblocked_verifier_count") != 20:
        raise VerificationError("passed unblocked verifier count drift")
    if result.get("blocked_safe_outcome_count") != 1:
        raise VerificationError("blocked safe-outcome count drift")
    if result.get("passed_unblocked_verifier_rate") != round(20 / 21, 4):
        raise VerificationError("passed unblocked verifier rate drift")
    if (
        result.get("task_completion_rate") is not None
        or result.get("task_completion_count") is not None
        or result.get("task_completion_posture") != "not_measured"
    ):
        raise VerificationError("task completion must remain not measured")
    projection = result.get("report_projection")
    if not isinstance(projection, dict):
        raise VerificationError("capability evaluation report projection is required")
    expected_projection = _expected_report_projection()
    if projection != expected_projection:
        raise VerificationError("capability evaluation report projection drift")
    projection_digest = _projection_digest(projection)
    if result.get("report_projection_digest") != projection_digest:
        raise VerificationError("capability evaluation report projection digest drift")
    if result.get("registry_fingerprint_ref") != evaluation_registry_fingerprint():
        raise VerificationError("capability evaluation registry fingerprint drift")
    for metric in (
        "correctness_rate",
        "recovery_success_rate",
        "evidence_completeness_rate",
        "replay_correctness_rate",
        "operator_intervention_count",
        "false_completion_count",
        "unsupported_claim_count",
        "authority_policy_violation_count",
    ):
        if result.get(metric) is not None or result.get(f"{metric}_posture") != "not_measured":
            raise VerificationError(f"unbound metric must remain not measured: {metric}")
    if result.get("cross_repo_empirical_performance") != "not_measured":
        raise VerificationError("cross-repository empirical result must remain not measured")
    if result.get("observed_product_experience") != "not_measured":
        raise VerificationError("observed product experience must remain not measured")
    return data


def verify(path: Path = DEFAULT_ARTIFACT) -> dict[str, Any]:
    payload = _safe_read(path.relative_to(ROOT), root=ROOT, maximum_bytes=MAX_ARTIFACT_BYTES)
    return verify_data(json.loads(payload.decode("utf-8")))


def main() -> int:
    verify()
    print("OK: UAA-GoatCitadel comparison findings are bounded and evidence-gated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
