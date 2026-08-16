#!/usr/bin/env python3
"""Verify the bounded, redacted UAA-GoatCitadel comparison artifact."""

from __future__ import annotations

import argparse
import json
import hashlib
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
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
    evaluation_report_projection,
    evaluation_registry_fingerprint,
    evaluation_source_commit_is_ancestor,
    evaluation_source_digest,
    evaluation_source_digest_at_commit,
    evaluation_source_paths,
    repository_commit,
    run_agent_capability_evaluation,
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
PROVENANCE_REPLACEMENT = (
    ROOT
    / "docs"
    / "benchmarks"
    / "runtime_capability_foundation"
    / "goat_comparison_20260712.provenance-0001.json"
)
PROVENANCE_REPLACEMENT_GLOB = "goat_comparison_20260712.provenance-*.json"
HISTORICAL_ARTIFACT_DIGEST = (
    "sha256:e5145cb1c1cbd92aa222d0d4fa19ca1def82b54e1593cc673cf8db433a97b751"
)
PROVENANCE_REPAIR_BASE_COMMIT = "5a07d3cff7a0d6cce5780378b8c1624bd8417d74"
PROVENANCE_TRANSITION_SOURCE_REFS = (
    "repo-ref:uaa:apps/control-center/src/App.test.tsx",
    "repo-ref:uaa:scripts/verify_goat_comparison_findings.py",
    "repo-ref:uaa:tests/test_goat_comparison_findings.py",
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
MAX_PROVENANCE_REPLACEMENT_BYTES = 16_384
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
            raise VerificationError(
                "comparison input must be a single-link regular file"
            )
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
            raise VerificationError(
                "comparison input changed or exceeded its size bound"
            )
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
    numerator = sum(
        _score(item[f"{system}_gates"]) * item["weight"] for item in findings
    )
    return round(numerator / 124 * 10, 4)


def _validate_external_root(root: Path) -> Path:
    if root.is_symlink() or not root.is_dir():
        raise VerificationError("external evidence root must be a real directory")
    return root.resolve(strict=True)


def _validate_evidence_ref(
    value: str,
    system: str,
    *,
    goat_root: Path | None,
) -> None:
    match = EVIDENCE_RE.fullmatch(value)
    if match is None or match.group(1) != system:
        raise VerificationError(f"invalid comparison evidence ref: {value}")
    relative = Path(match.group(2))
    if relative.is_absolute() or ".." in relative.parts:
        raise VerificationError("comparison evidence path is unsafe")
    if system == "goatcitadel" and goat_root is None:
        return
    repo_root = ROOT if system == "uaa" else goat_root
    if repo_root is None:
        raise VerificationError("external comparison evidence root is required")
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


def _validate_report_projection(
    projection: dict[str, Any],
    result: dict[str, Any],
) -> None:
    phase09_bindings = [
        (
            spec.scenario_id,
            spec.component_id,
            spec.expected_status,
            scenario_execution_fingerprint(spec),
        )
        for spec in PHASE09_SCENARIOS
    ]
    additional_bindings = [
        (
            spec.scenario_ref,
            spec.component_id,
            "passed",
            _scenario_fingerprint(spec),
        )
        for spec in ADDITIONAL_SCENARIOS
    ]
    expected_bindings = (*phase09_bindings, *additional_bindings)
    observations = projection.get("observations")
    if not isinstance(observations, list) or len(observations) != len(
        expected_bindings
    ):
        raise VerificationError("capability evaluation observation coverage drift")
    for observation, expected in zip(observations, expected_bindings, strict=True):
        if not isinstance(observation, dict):
            raise VerificationError("capability evaluation observation shape drift")
        binding = (
            observation.get("scenario_ref"),
            observation.get("component_id"),
            observation.get("expected_status"),
            observation.get("execution_fingerprint_ref"),
        )
        if binding != expected:
            raise VerificationError("capability evaluation observation binding drift")
        observed_status = observation.get("observed_status")
        failure_code = observation.get("failure_code")
        if observed_status not in {"passed", "blocked", "failed"}:
            raise VerificationError("capability evaluation observed status drift")
        if (observed_status == "failed") != (failure_code != "none"):
            raise VerificationError("capability evaluation failure posture drift")
        for metric in (
            "evidence_complete",
            "task_completed",
            "completion_claimed",
            "operator_interventions",
            "unsupported_claim_count",
            "policy_violation_refs",
            "recovery_succeeded",
            "replay_succeeded",
        ):
            if observation.get(metric) is not None:
                raise VerificationError(
                    "verifier exit status cannot synthesize semantic observation truth"
                )
    adherence_count = sum(
        item["observed_status"] == item["expected_status"] for item in observations
    )
    passed_unblocked_count = sum(
        item["expected_status"] == "passed" and item["observed_status"] == "passed"
        for item in observations
    )
    blocked_count = sum(item["observed_status"] == "blocked" for item in observations)
    expected_summary = {
        "scenario_count": len(observations),
        "safe_outcome_adherence_rate": round(adherence_count / len(observations), 4),
        "verification_pass_rate": round(adherence_count / len(observations), 4),
        "passed_unblocked_verifier_rate": round(
            passed_unblocked_count / len(observations), 4
        ),
        "passed_unblocked_verifier_count": passed_unblocked_count,
        "blocked_safe_outcome_count": blocked_count,
    }
    for key, value in expected_summary.items():
        if projection.get(key) != value or result.get(key) != value:
            raise VerificationError(f"capability evaluation {key} drift")
    if projection.get("registry_fingerprint_ref") != evaluation_registry_fingerprint():
        raise VerificationError("capability evaluation registry projection drift")
    if projection.get("component_ids") != list(COMPONENT_IDS):
        raise VerificationError("capability evaluation component projection drift")
    if projection.get("content_free") is not True:
        raise VerificationError("capability evaluation projection is not content-free")
    if projection.get("authority_granted") is not False:
        raise VerificationError("capability evaluation projection grants authority")


def _projection_digest(projection: dict[str, Any]) -> str:
    encoded = json.dumps(projection, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _sha256_ref(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _load_provenance_replacement() -> dict[str, Any]:
    candidates = tuple(
        sorted(PROVENANCE_REPLACEMENT.parent.glob(PROVENANCE_REPLACEMENT_GLOB))
    )
    if candidates != (PROVENANCE_REPLACEMENT,):
        raise VerificationError(
            "comparison provenance requires exactly one bounded generation"
        )
    payload = _safe_read(
        PROVENANCE_REPLACEMENT.relative_to(ROOT),
        root=ROOT,
        maximum_bytes=MAX_PROVENANCE_REPLACEMENT_BYTES,
    )
    return json.loads(payload.decode("utf-8"))


def _evaluation_source_changed_refs_at_commit(commit: str) -> tuple[str, ...]:
    changed: list[str] = []
    for relative in evaluation_source_paths():
        result = subprocess.run(
            ("/usr/bin/git", "cat-file", "blob", f"{commit}:{relative}"),
            cwd=ROOT,
            env={
                "PATH": "/usr/bin:/bin",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": "/dev/null",
            },
            capture_output=True,
            check=False,
            timeout=5,
        )
        if result.returncode != 0:
            raise VerificationError(
                "reachable replacement source envelope is unavailable"
            )
        current = _safe_read(
            Path(relative), root=ROOT, maximum_bytes=MAX_EVIDENCE_BYTES
        )
        if current != result.stdout:
            changed.append(f"repo-ref:uaa:{relative}")
    return tuple(changed)


def _validate_provenance_replacement(
    data: dict[str, Any], replacement: dict[str, Any]
) -> None:
    _walk(replacement)
    if contains_secret_like(replacement) or contains_obvious_secret(replacement):
        raise VerificationError("comparison provenance contains secret-like material")
    if set(replacement) != {
        "schema_version",
        "generation",
        "comparison_artifact",
        "historical_binding",
        "reachable_replacement",
        "contract_transition",
        "retention_posture",
        "generation_posture",
        "cross_surface_parity",
        "reason_ref",
        "authority_granted",
    }:
        raise VerificationError("comparison provenance replacement shape drift")
    if (
        replacement.get("schema_version")
        != "uaa_goat_comparison_provenance_replacement.v1"
        or replacement.get("generation") != 1
    ):
        raise VerificationError("comparison provenance generation drift")
    if replacement.get("authority_granted") is not False:
        raise VerificationError("comparison provenance cannot grant authority")
    if replacement.get("retention_posture") != "append_only_predecessor_retained":
        raise VerificationError("comparison provenance retention drift")
    if replacement.get("generation_posture") != "single_generation_fail_closed":
        raise VerificationError("comparison provenance generation posture drift")
    if replacement.get("cross_surface_parity") != "not_applicable_provenance_only":
        raise VerificationError("comparison provenance parity posture drift")
    if replacement.get("reason_ref") != (
        "reason-ref:goat-comparison-orphaned-squash-source-binding"
    ):
        raise VerificationError("comparison provenance reason drift")

    historical_payload = _safe_read(
        DEFAULT_ARTIFACT.relative_to(ROOT),
        root=ROOT,
        maximum_bytes=MAX_ARTIFACT_BYTES,
    )
    artifact = replacement.get("comparison_artifact")
    if not isinstance(artifact, dict) or artifact != {
        "artifact_ref": "artifact-ref:uaa-goat-comparison:20260712",
        "artifact_sha256": HISTORICAL_ARTIFACT_DIGEST,
        "immutable": True,
    }:
        raise VerificationError("comparison artifact replacement binding drift")
    if _sha256_ref(historical_payload) != HISTORICAL_ARTIFACT_DIGEST:
        raise VerificationError("historical comparison artifact substitution")

    result = data.get("implementation_result", {})
    historical = replacement.get("historical_binding")
    if not isinstance(historical, dict):
        raise VerificationError("historical comparison source binding is required")
    source_commit = result.get("uaa_source_commit")
    if not isinstance(source_commit, str) or not re.fullmatch(
        r"[0-9a-f]{40}", source_commit
    ):
        raise VerificationError("exact UAA evaluation source commit is required")
    if historical != {
        "source_commit": source_commit,
        "evaluator_source_digest": result.get("evaluator_source_digest"),
        "evaluator_source_file_count": result.get("evaluator_source_file_count"),
        "posture": "historical_unreachable_or_missing_from_fresh_main",
    }:
        raise VerificationError("historical evaluator source digest substitution")

    reachable = replacement.get("reachable_replacement")
    if not isinstance(reachable, dict) or set(reachable) != {
        "source_commit",
        "evaluator_source_digest",
        "evaluator_source_file_count",
        "posture",
    }:
        raise VerificationError("reachable comparison replacement shape drift")
    replacement_commit = reachable.get("source_commit")
    if replacement_commit != PROVENANCE_REPAIR_BASE_COMMIT:
        raise VerificationError("reachable comparison source commit substitution")
    if reachable.get("posture") != "reachable_ancestor_digest_equivalent":
        raise VerificationError("reachable comparison source posture drift")
    if not evaluation_source_commit_is_ancestor(replacement_commit):
        raise VerificationError(
            "replacement UAA evaluation source commit is not reachable"
        )
    replacement_digest = evaluation_source_digest_at_commit(replacement_commit)
    if reachable.get("evaluator_source_digest") != replacement_digest:
        raise VerificationError("reachable comparison source digest drift")
    if reachable.get("evaluator_source_file_count") != len(evaluation_source_paths()):
        raise VerificationError("reachable comparison source coverage drift")
    if historical.get("evaluator_source_digest") != replacement_digest:
        raise VerificationError(
            "historical and reachable comparison sources are not digest equivalent"
        )

    transition = replacement.get("contract_transition")
    if not isinstance(transition, dict) or set(transition) != {
        "current_evaluator_source_digest",
        "current_evaluator_source_file_count",
        "changed_source_refs",
        "posture",
        "comparison_findings_changed",
        "score_changed",
        "report_projection_changed",
    }:
        raise VerificationError("comparison provenance transition shape drift")
    if transition.get("current_evaluator_source_digest") != evaluation_source_digest():
        raise VerificationError(
            "stored capability evidence is stale for the current evaluator source"
        )
    if transition.get("current_evaluator_source_file_count") != len(
        evaluation_source_paths()
    ):
        raise VerificationError("current capability evaluator source coverage drift")
    expected_changed_refs = _evaluation_source_changed_refs_at_commit(
        replacement_commit
    )
    if expected_changed_refs != PROVENANCE_TRANSITION_SOURCE_REFS:
        raise VerificationError("unbounded comparison provenance source transition")
    if transition.get("changed_source_refs") != list(expected_changed_refs):
        raise VerificationError("comparison provenance source substitution")
    if transition.get("posture") != (
        "provenance_verifier_only_no_runtime_evaluator_change"
    ):
        raise VerificationError("comparison provenance transition posture drift")
    for field in (
        "comparison_findings_changed",
        "score_changed",
        "report_projection_changed",
    ):
        if transition.get(field) is not False:
            raise VerificationError(
                "comparison provenance cannot change evidence truth"
            )


def verify_data(
    data: dict[str, Any],
    *,
    goat_root: Path | None = None,
    revalidate_uaa: bool = False,
    provenance_replacement: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if goat_root is not None:
        goat_root = _validate_external_root(goat_root)
    _walk(data)
    if contains_secret_like(data) or contains_obvious_secret(data):
        raise VerificationError("comparison contains secret-like material")
    if data.get("schema_version") != "uaa_goat_comparison_findings.v1":
        raise VerificationError("comparison schema drift")
    if data.get("authority_granted") is not False:
        raise VerificationError("comparison cannot grant authority")
    findings = data.get("findings")
    if (
        not isinstance(findings, list)
        or tuple(item.get("component") for item in findings) != COMPONENT_IDS
    ):
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
                raise VerificationError(
                    "every comparison component requires evidence refs"
                )
            for value in values:
                _validate_evidence_ref(value, system, goat_root=goat_root)
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
            item["component"]: _score(item[f"{system}_gates"]) for item in findings
        }
        if component_scores != expected_scores:
            raise VerificationError(f"{system} initial component score drift")
    if data.get("final_scores") != initial:
        raise VerificationError("final scores changed without new bound evidence gates")

    result = data.get("implementation_result", {})
    expected_scenario_count = len(PHASE09_SCENARIOS) + len(ADDITIONAL_SCENARIOS)
    expected_passed_count = sum(
        spec.expected_status == "passed" for spec in PHASE09_SCENARIOS
    ) + len(ADDITIONAL_SCENARIOS)
    expected_blocked_count = sum(
        spec.expected_status == "blocked" for spec in PHASE09_SCENARIOS
    )
    if (
        result.get("scenario_count") != expected_scenario_count
        or result.get("component_count") != 16
    ):
        raise VerificationError("capability evaluation coverage drift")
    if result.get("safe_outcome_adherence_rate") != 1:
        raise VerificationError("safe-outcome adherence drift")
    if result.get("verification_pass_rate") != 1:
        raise VerificationError("scenario verifier pass-rate drift")
    if result.get("passed_unblocked_verifier_count") != expected_passed_count:
        raise VerificationError("passed unblocked verifier count drift")
    if result.get("blocked_safe_outcome_count") != expected_blocked_count:
        raise VerificationError("blocked safe-outcome count drift")
    if result.get("passed_unblocked_verifier_rate") != round(
        expected_passed_count / expected_scenario_count, 4
    ):
        raise VerificationError("passed unblocked verifier rate drift")
    if (
        any(
            result.get(key) is not None
            for key in ("task_completion_rate", "task_completion_count")
        )
        or result.get("task_completion_posture") != "not_measured"
    ):
        raise VerificationError("task completion must remain not measured")
    projection = result.get("report_projection")
    if not isinstance(projection, dict):
        raise VerificationError("capability evaluation report projection is required")
    _validate_report_projection(projection, result)
    projection_digest = _projection_digest(projection)
    if result.get("report_projection_digest") != projection_digest:
        raise VerificationError("capability evaluation report projection digest drift")
    if result.get("registry_fingerprint_ref") != evaluation_registry_fingerprint():
        raise VerificationError("capability evaluation registry fingerprint drift")
    _validate_provenance_replacement(
        data,
        provenance_replacement
        if provenance_replacement is not None
        else _load_provenance_replacement(),
    )
    if result.get("runtime_revalidation_required") is not True:
        raise VerificationError("runtime revalidation posture drift")
    if result.get("external_evidence_posture") != "opt_in_root_required":
        raise VerificationError("external evidence revalidation posture drift")
    unmeasured_metrics = (
        "correctness_rate",
        "recovery_success_rate",
        "evidence_completeness_rate",
        "replay_correctness_rate",
        "operator_intervention_count",
        "false_completion_count",
        "unsupported_claim_count",
        "authority_policy_violation_count",
    )
    for metric in unmeasured_metrics:
        if (
            result.get(metric) is not None
            or result.get(f"{metric}_posture") != "not_measured"
        ):
            raise VerificationError(
                f"capability metric must remain not measured: {metric}"
            )
    if result.get("cross_repo_empirical_performance") != "not_measured":
        raise VerificationError(
            "cross-repository empirical result must remain not measured"
        )
    if result.get("observed_product_experience") != "not_measured":
        raise VerificationError("observed product experience must remain not measured")
    if revalidate_uaa:
        actual_projection = evaluation_report_projection(
            run_agent_capability_evaluation()
        )
        if actual_projection != projection:
            raise VerificationError(
                "stored capability projection does not match current runtime evaluation"
            )
    return data


def verify(
    path: Path = DEFAULT_ARTIFACT,
    *,
    goat_root: Path | None = None,
    revalidate_uaa: bool = False,
) -> dict[str, Any]:
    if path != DEFAULT_ARTIFACT:
        raise VerificationError("comparison verification path is not canonical")
    payload = _safe_read(
        path.relative_to(ROOT), root=ROOT, maximum_bytes=MAX_ARTIFACT_BYTES
    )
    return verify_data(
        json.loads(payload.decode("utf-8")),
        goat_root=goat_root,
        revalidate_uaa=revalidate_uaa,
        provenance_replacement=_load_provenance_replacement(),
    )


def refresh_uaa_evaluation(path: Path = DEFAULT_ARTIFACT) -> dict[str, Any]:
    if path != DEFAULT_ARTIFACT or not path.is_file() or path.is_symlink():
        raise VerificationError(
            "comparison artifact refresh path is not canonical and regular"
        )
    status = subprocess.run(
        ("/usr/bin/git", "status", "--porcelain=v1", "--untracked-files=all"),
        cwd=ROOT,
        env={
            "PATH": "/usr/bin:/bin",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
        },
        capture_output=True,
        check=False,
        timeout=10,
    )
    if status.returncode != 0 or status.stdout:
        raise VerificationError(
            "comparison artifact refresh requires an exact clean committed worktree"
        )
    if PROVENANCE_REPLACEMENT.exists():
        raise VerificationError(
            "historical comparison artifact is immutable; create a new bounded artifact"
        )
    data = json.loads(
        _safe_read(path.relative_to(ROOT), root=ROOT, maximum_bytes=MAX_ARTIFACT_BYTES)
    )
    report = run_agent_capability_evaluation()
    projection = evaluation_report_projection(report)
    result = data.get("implementation_result")
    if not isinstance(result, dict):
        raise VerificationError("comparison implementation result is required")
    result.update(
        {
            "status": "implemented",
            "scenario_count": report.scenario_count,
            "component_count": report.component_count,
            "safe_outcome_adherence_rate": report.safe_outcome_adherence_rate,
            "verification_pass_rate": report.verification_pass_rate,
            "passed_unblocked_verifier_rate": report.passed_unblocked_verifier_rate,
            "passed_unblocked_verifier_count": report.passed_unblocked_verifier_count,
            "task_completion_rate": report.task_completion_rate,
            "task_completion_count": report.task_completion_count,
            "task_completion_posture": report.task_completion_posture,
            "blocked_safe_outcome_count": report.blocked_safe_outcome_count,
            "correctness_rate": report.correctness_rate,
            "correctness_rate_posture": report.correctness_posture,
            "recovery_success_rate": report.recovery_success_rate,
            "recovery_success_rate_posture": report.recovery_posture,
            "evidence_completeness_rate": report.evidence_completeness_rate,
            "evidence_completeness_rate_posture": report.evidence_completeness_posture,
            "replay_correctness_rate": report.replay_correctness_rate,
            "replay_correctness_rate_posture": report.replay_correctness_posture,
            "operator_intervention_count": report.operator_intervention_count,
            "operator_intervention_count_posture": report.operator_intervention_posture,
            "false_completion_count": report.false_completion_count,
            "false_completion_count_posture": report.false_completion_posture,
            "unsupported_claim_count": report.unsupported_claim_count,
            "unsupported_claim_count_posture": report.unsupported_claim_posture,
            "authority_policy_violation_count": report.authority_policy_violation_count,
            "authority_policy_violation_count_posture": report.authority_policy_violation_posture,
            "content_free": report.content_free,
            "uaa_source_commit": repository_commit(),
            "evaluator_source_digest": evaluation_source_digest(),
            "evaluator_source_file_count": len(evaluation_source_paths()),
            "registry_fingerprint_ref": evaluation_registry_fingerprint(),
            "report_projection_digest": _projection_digest(projection),
            "report_projection": projection,
        }
    )
    verify_data(data)
    encoded = (json.dumps(data, indent=2, sort_keys=False) + "\n").encode("utf-8")
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=path.parent,
        prefix=".goat-comparison-refresh-",
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.chmod(temp_path, 0o644)
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--goat-root",
        type=Path,
        help="Explicit read-only GoatCitadel evidence root for opt-in line validation.",
    )
    parser.add_argument(
        "--revalidate-uaa",
        action="store_true",
        help="Run the bounded UAA evaluator and compare it with the stored projection.",
    )
    parser.add_argument(
        "--refresh-uaa-evaluation",
        action="store_true",
        help="Refresh only the content-free UAA evaluation projection in the canonical artifact.",
    )
    args = parser.parse_args(argv)
    if args.refresh_uaa_evaluation:
        if args.goat_root is not None or args.revalidate_uaa:
            parser.error(
                "refresh cannot be combined with external or revalidation options"
            )
        refresh_uaa_evaluation()
    else:
        verify(goat_root=args.goat_root, revalidate_uaa=args.revalidate_uaa)
    print("OK: UAA-GoatCitadel comparison findings are bounded and evidence-gated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
