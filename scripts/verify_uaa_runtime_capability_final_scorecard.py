#!/usr/bin/env python3
"""Verify the finite Phase 09 UAA/GoatCitadel capability scorecard."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.verify_uaa_runtime_capability_scoreboard import (  # noqa: E402
    EXPECTED_COMPONENTS,
    EXPECTED_WEIGHTS,
)
from scripts.verify_uaa_runtime_phase09_benchmark import (  # noqa: E402
    verify as verify_scenarios,
)


FINAL_SCORECARD = (
    ROOT
    / "docs"
    / "benchmarks"
    / "runtime_capability_foundation"
    / "phase09_final_scorecard.json"
)
BASELINE = (
    ROOT
    / "docs"
    / "benchmarks"
    / "runtime_capability_foundation"
    / "phase00_baseline.json"
)
SCENARIOS = (
    ROOT
    / "docs"
    / "benchmarks"
    / "runtime_capability_foundation"
    / "phase09_scenario_results.json"
)
FINAL_REPORT = (
    ROOT
    / "docs"
    / "control_center"
    / "UAA_RUNTIME_CAPABILITY_FINAL_SCORECARD.md"
)
UAA_REF_RE = re.compile(r"^repo-ref:uaa:([^#]+)(?:#L\d+(?:-L?\d+)?)?$")
GOAT_REF_RE = re.compile(
    r"^repo-ref:goatcitadel:v1\.0\.0:([^#]+)(?:#L\d+(?:-L?\d+)?)?$"
)
ABSOLUTE_PATH_RE = re.compile(
    r"(?:/Users/|/home/|/private/|/var/|/tmp/|[A-Za-z]:\\)"
)
SECRET_RE = re.compile(
    r"(?:api[_-]?key|secret|password|credential|access[_-]?token)\s*[:=]",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
URL_RE = re.compile(r"\b(?:https?|file)://", re.IGNORECASE)
HOST_RE = re.compile(
    r"\b(?:localhost|(?:[A-Za-z0-9-]+\.)+(?:com|net|org|io|dev|local|internal))\b",
    re.IGNORECASE,
)
INJECTION_RE = re.compile(
    r"(?:ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions|"
    r"system\s+prompt|developer\s+message|<script\b)",
    re.IGNORECASE,
)
OPAQUE_REPAIR_REF_RE = re.compile(r"^repair-pass-ref:[a-z0-9][a-z0-9:._-]{2,255}$")
OPAQUE_UNRESOLVED_REF_RE = re.compile(r"^unresolved-ref:[a-z0-9][a-z0-9:._-]{2,255}$")
GIT_SHA_RE = re.compile(r"^git-sha:[0-9a-f]{40}$")
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?$")
EXPECTED_COMPONENT_EVIDENCE = {
    "reasoning_task_understanding": {
        "uaa": (
            "repo-ref:uaa:src/ultimate_ai_agent/core/intent/reasoning_truth.py",
            "repo-ref:uaa:tests/test_phase01_reasoning_truth.py",
            "repo-ref:uaa:apps/control-center/src/components/FounderLoopPanels.tsx",
        ),
        "goatcitadel": (
            "repo-ref:goatcitadel:v1.0.0:apps/gateway/src/services/chat-agent-orchestrator.test.ts",
        ),
    },
    "planning_orchestration": {
        "uaa": (
            "repo-ref:uaa:src/ultimate_ai_agent/core/execution/mission_orchestrator.py",
            "repo-ref:uaa:tests/test_authority_mission_orchestrator_hardening.py",
            "repo-ref:uaa:apps/control-center/src/components/AuthorityMissionInspectionPanel.tsx",
        ),
        "goatcitadel": (
            "repo-ref:goatcitadel:v1.0.0:apps/gateway/src/services/durable-run-service.boot-recovery.integration.test.ts",
        ),
    },
    "learning_adaptation": {
        "uaa": (
            "repo-ref:uaa:src/ultimate_ai_agent/core/memory/review_runtime.py",
            "repo-ref:uaa:tests/test_governed_memory_context_phase03.py",
            "repo-ref:uaa:apps/control-center/src/components/FounderLoopPanels.tsx",
        ),
        "goatcitadel": (
            "repo-ref:goatcitadel:v1.0.0:apps/gateway/src/services/memory-lifecycle-policy.test.ts",
        ),
    },
    "memory_context_management": {
        "uaa": (
            "repo-ref:uaa:src/ultimate_ai_agent/core/memory/governed_context.py",
            "repo-ref:uaa:tests/test_governed_memory_context_phase03.py",
            "repo-ref:uaa:apps/control-center/src/components/FounderLoopPanels.tsx",
        ),
        "goatcitadel": (
            "repo-ref:goatcitadel:v1.0.0:packages/memory-core/src/context-composer.ts",
        ),
    },
    "communication_interaction": {
        "uaa": (
            "repo-ref:uaa:src/ultimate_ai_agent/core/control_center/agent_loop.py",
            "repo-ref:uaa:tests/test_runtime_agent_loop_spine.py",
            "repo-ref:uaa:apps/control-center/src/components/FounderLoopPanels.tsx",
        ),
        "goatcitadel": (
            "repo-ref:goatcitadel:v1.0.0:apps/mission-control-next/src/features/threaded-surface/ThreadedSurfacePage.test.tsx",
        ),
    },
    "action_tool_calling": {
        "uaa": (
            "repo-ref:uaa:src/ultimate_ai_agent/core/authority/dispatcher.py",
            "repo-ref:uaa:tests/test_authority_dispatcher_approval_and_start.py",
            "repo-ref:uaa:apps/control-center/src/components/FounderLoopPanels.tsx",
        ),
        "goatcitadel": (
            "repo-ref:goatcitadel:v1.0.0:apps/gateway/src/services/tool-invocation-coordinator-service.test.ts",
        ),
    },
    "autonomy_authority": {
        "uaa": (
            "repo-ref:uaa:src/ultimate_ai_agent/core/authority/contracts.py",
            "repo-ref:uaa:tests/test_authority_mission_controls.py",
            "repo-ref:uaa:apps/control-center/src/components/OperatorFlowPanels.tsx",
        ),
        "goatcitadel": (
            "repo-ref:goatcitadel:v1.0.0:apps/gateway/src/services/approval-runtime-service.test.ts",
        ),
    },
    "code_implementation_assistance": {
        "uaa": (
            "repo-ref:uaa:src/ultimate_ai_agent/core/control_center/action_tool_code_catalog.py",
            "repo-ref:uaa:tests/test_runtime_action_tool_code_lanes.py",
            "repo-ref:uaa:apps/control-center/src/components/CodingCockpitPanel.tsx",
        ),
        "goatcitadel": (
            "repo-ref:goatcitadel:v1.0.0:apps/gateway/src/services/code-mode-sandbox/linux-firejail-adapter.security.test.ts",
        ),
    },
    "research_web_external": {
        "uaa": (
            "repo-ref:uaa:src/ultimate_ai_agent/core/web_access/research_aggregation.py",
            "repo-ref:uaa:tests/test_web_research_aggregation.py",
            "repo-ref:uaa:apps/control-center/src/components/CapabilitySurfacePanel.tsx",
        ),
        "goatcitadel": (
            "repo-ref:goatcitadel:v1.0.0:apps/gateway/src/routes/research-search.test.ts",
        ),
    },
    "model_provider_management": {
        "uaa": (
            "repo-ref:uaa:src/ultimate_ai_agent/core/capability_availability/read_model.py",
            "repo-ref:uaa:tests/test_capability_availability.py",
            "repo-ref:uaa:apps/control-center/src/components/FounderLoopPanels.tsx",
        ),
        "goatcitadel": (
            "repo-ref:goatcitadel:v1.0.0:apps/gateway/src/services/llm-runtime-truth-service.test.ts",
        ),
    },
    "evidence_audit_observability": {
        "uaa": (
            "repo-ref:uaa:src/ultimate_ai_agent/core/execution/portable_mission_evidence.py",
            "repo-ref:uaa:tests/test_portable_mission_evidence.py",
            "repo-ref:uaa:apps/control-center/src/components/AuthorityMissionInspectionPanel.tsx",
        ),
        "goatcitadel": (
            "repo-ref:goatcitadel:v1.0.0:apps/gateway/src/services/evidence-envelope-service.test.ts",
        ),
    },
    "safety_security_failure": {
        "uaa": (
            "repo-ref:uaa:src/ultimate_ai_agent/core/authority/dispatcher.py",
            "repo-ref:uaa:tests/test_authority_mission_controls.py",
            "repo-ref:uaa:apps/control-center/src/api/redaction.test.ts",
        ),
        "goatcitadel": (
            "repo-ref:goatcitadel:v1.0.0:packages/policy-engine/src/tool-executor.test.ts",
        ),
    },
    "ux_ai_cockpit": {
        "uaa": (
            "repo-ref:uaa:src/ultimate_ai_agent/core/control_center/agent_loop.py",
            "repo-ref:uaa:tests/test_runtime_agent_loop_spine.py",
            "repo-ref:uaa:apps/control-center/src/App.test.tsx",
        ),
        "goatcitadel": (
            "repo-ref:goatcitadel:v1.0.0:apps/mission-control-next/src/features/native-routes/ops/RunDetailRoutePage.test.tsx",
        ),
    },
    "cli_api_parity": {
        "uaa": (
            "repo-ref:uaa:src/ultimate_ai_agent/api/manifest.py",
            "repo-ref:uaa:tests/test_api_manifest.py",
            "repo-ref:uaa:scripts/verify_uaa_runtime_cockpit_cli_api.py",
        ),
        "goatcitadel": (
            "repo-ref:goatcitadel:v1.0.0:apps/gateway/src/admin-cli.integration.test.ts",
        ),
    },
    "extensibility_ecosystem": {
        "uaa": (
            "repo-ref:uaa:src/ultimate_ai_agent/core/extension_catalog/contracts.py",
            "repo-ref:uaa:tests/test_inspectable_extension_catalog.py",
            "repo-ref:uaa:apps/control-center/src/components/CapabilitySurfacePanel.tsx",
        ),
        "goatcitadel": (
            "repo-ref:goatcitadel:v1.0.0:packages/extensions-sdk/src/integration-plugins.test.ts",
        ),
    },
    "productized_agent_loop": {
        "uaa": (
            "repo-ref:uaa:src/ultimate_ai_agent/core/control_center/founder_loop_mission.py",
            "repo-ref:uaa:tests/test_founder_loop_filesystem_mission.py",
            "repo-ref:uaa:apps/control-center/src/components/FounderLoopPanels.tsx",
        ),
        "goatcitadel": (
            "repo-ref:goatcitadel:v1.0.0:apps/mission-control-next/src/features/threaded-surface/ThreadedWorkflowPanel.test.tsx",
        ),
    },
}
TOP_LEVEL_KEYS = {
    "schema_version",
    "scorecard_ref",
    "status",
    "authority_granted",
    "baseline",
    "comparison",
    "scoring",
    "components",
    "weighted_totals",
    "scenario_results",
    "repair_passes",
    "unresolved_items",
    "redaction",
}
COMPONENT_KEYS = {
    "component_id",
    "label",
    "weight",
    "phase_owner",
    "before_score",
    "uaa",
    "goatcitadel",
}
ASSESSMENT_KEYS = {
    "score",
    "status",
    "confidence",
    "evidence_refs",
    "gap",
    "recommendation",
}
SAFE_STATUSES = {
    "implemented",
    "partial",
    "planned",
    "mock-only",
    "blocked",
    "deprecated",
    "contradicted",
    "unknown",
}
TERMINAL_CLASSIFICATIONS = {
    "blocked",
    "unsupported",
    "adapter required",
    "configuration required",
    "external facility required",
    "deferred by authority policy",
}
REDACTION = {
    "safe_refs_only": True,
    "raw_content_persisted": False,
    "local_paths_persisted": False,
    "machine_identity_persisted": False,
}


class VerificationError(RuntimeError):
    """Raised when the final scorecard drifts from finite evidence truth."""


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(_read_bounded_bytes(path)).hexdigest()}"


def _read_bounded_bytes(path: Path, *, max_bytes: int = 1_000_000) -> bytes:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    try:
        for part in absolute.parts[1:-1]:
            current /= part
            if stat.S_ISLNK(os.lstat(current).st_mode):
                raise VerificationError("final artifact parent must not be a symlink")
    except FileNotFoundError as exc:
        raise VerificationError("required final artifact is missing") from exc
    try:
        path_stat = os.lstat(path)
    except FileNotFoundError as exc:
        raise VerificationError("required final artifact is missing") from exc
    if stat.S_ISLNK(path_stat.st_mode) or not stat.S_ISREG(path_stat.st_mode):
        raise VerificationError("final artifact must be a regular non-symlink file")
    resolved = path.resolve()
    if ROOT.resolve() not in {resolved, *resolved.parents}:
        raise VerificationError("final artifact must remain inside the repository")
    if path_stat.st_size > max_bytes:
        raise VerificationError("final artifact exceeds the size limit")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    try:
        opened_stat = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened_stat.st_mode)
            or opened_stat.st_dev != path_stat.st_dev
            or opened_stat.st_ino != path_stat.st_ino
            or opened_stat.st_size > max_bytes
        ):
            raise VerificationError("final artifact changed during bounded open")
        encoded = os.read(descriptor, max_bytes + 1)
    finally:
        os.close(descriptor)
    if len(encoded) > max_bytes:
        raise VerificationError("final artifact exceeds the size limit")
    return encoded


def _read_bounded_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(_read_bounded_bytes(path).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError("final JSON artifact is invalid") from exc
    if not isinstance(data, dict):
        raise VerificationError("final JSON artifact must be an object")
    return data


def _validate_safe_free_text(value: Any, label: str, *, max_length: int = 1200) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > max_length:
        raise VerificationError(f"{label} must be bounded non-empty text")
    if any(unicodedata.category(character) in {"Cc", "Cf"} for character in value):
        raise VerificationError(f"{label} contains control or formatting characters")
    if (
        ABSOLUTE_PATH_RE.search(value)
        or SECRET_RE.search(value)
        or EMAIL_RE.search(value)
        or URL_RE.search(value)
        or HOST_RE.search(value)
        or INJECTION_RE.search(value)
    ):
        raise VerificationError(f"{label} contains unsafe text")


def _validate_safe_report_text(value: str) -> None:
    if any(
        unicodedata.category(character) == "Cf"
        or (
            unicodedata.category(character) == "Cc"
            and character not in {"\n", "\r", "\t"}
        )
        for character in value
    ):
        raise VerificationError("final report contains unsafe controls")
    if (
        ABSOLUTE_PATH_RE.search(value)
        or SECRET_RE.search(value)
        or EMAIL_RE.search(value)
        or URL_RE.search(value)
        or HOST_RE.search(value)
        or INJECTION_RE.search(value)
    ):
        raise VerificationError("final report contains unsafe text")


def _walk(value: Any, key: str | None = None) -> None:
    if key in {
        "raw_prompt",
        "raw_response",
        "raw_result",
        "raw_page",
        "raw_log",
        "provider_payload",
        "credential",
        "secret",
        "token",
        "username",
        "hostname",
        "environment_dump",
        "local_path",
    }:
        raise VerificationError(f"unsafe durable field: {key}")
    if isinstance(value, dict):
        for child_key, child in value.items():
            _walk(child, child_key)
    elif isinstance(value, list):
        for child in value:
            _walk(child, key)
    elif isinstance(value, str):
        if ABSOLUTE_PATH_RE.search(value):
            raise VerificationError("absolute local path is forbidden")
        if SECRET_RE.search(value):
            raise VerificationError("secret-like value is forbidden")


def _require_keys(value: Any, keys: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise VerificationError(f"{label} keys drift")


def _validate_ref(ref: str, *, system: str) -> str:
    match = UAA_REF_RE.fullmatch(ref) if system == "uaa" else GOAT_REF_RE.fullmatch(ref)
    if match is None:
        raise VerificationError(f"unsupported {system} evidence ref")
    relative = Path(match.group(1))
    if relative.is_absolute() or ".." in relative.parts:
        raise VerificationError(f"unsafe {system} evidence ref")
    if system == "uaa" and not (ROOT / relative).is_file():
        raise VerificationError(f"missing UAA evidence ref: {ref}")
    if system == "uaa":
        current = ROOT
        for part in relative.parts:
            current /= part
            target_stat = os.lstat(current)
            if stat.S_ISLNK(target_stat.st_mode):
                raise VerificationError(f"unsafe UAA evidence ref: {ref}")
        if stat.S_ISLNK(target_stat.st_mode) or not stat.S_ISREG(target_stat.st_mode):
            raise VerificationError(f"unsafe UAA evidence ref: {ref}")
    return relative.as_posix()


def _weighted_total(components: list[dict[str, Any]], system: str) -> Decimal:
    numerator = sum(
        Decimal(str(row[system]["score"])) * Decimal(row["weight"])
        for row in components
    )
    return (numerator / Decimal(124) * Decimal(10)).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )


def verify_data(data: dict[str, Any]) -> None:
    _walk(data)
    _require_keys(data, TOP_LEVEL_KEYS, "top-level final scorecard")
    if data["schema_version"] != "uaa_runtime_capability_final_scorecard.v1":
        raise VerificationError("final schema version drift")
    if data["scorecard_ref"] != "scorecard-ref:runtime-capability-foundation:phase09-final":
        raise VerificationError("final scorecard ref drift")
    if data["status"] != "evidence_backed_final_bounded_stop":
        raise VerificationError("final status drift")
    if data["authority_granted"] is not False:
        raise VerificationError("scorecard cannot grant authority")

    baseline_data = _read_bounded_json(BASELINE)
    _require_keys(
        data["baseline"],
        {"artifact_ref", "artifact_sha256", "uaa_score", "goatcitadel_score"},
        "baseline binding",
    )
    if data["baseline"] != {
        "artifact_ref": "repo-ref:uaa:docs/benchmarks/runtime_capability_foundation/phase00_baseline.json",
        "artifact_sha256": _sha256(BASELINE),
        "uaa_score": baseline_data["weighted_totals"]["uaa"],
        "goatcitadel_score": baseline_data["weighted_totals"]["goatcitadel"],
    }:
        raise VerificationError("Phase 00 baseline binding drift")

    comparison = data["comparison"]
    _require_keys(
        comparison,
        {"uaa", "goatcitadel_release", "goatcitadel_local_head_observation"},
        "comparison",
    )
    if comparison["uaa"] != {
        "version": "0.104.0",
        "implementation_commit_ref": "git-sha:d5eca61ee586ffc06b699ee196f8cd1af0702563",
    }:
        raise VerificationError("UAA implementation baseline drift")
    if comparison["goatcitadel_release"] != {
        "version": "1.0.0",
        "tag_ref": "git-tag:v1.0.0",
        "commit_ref": "git-sha:dff26c018b44c394c189c170265a00ab640f1214",
        "inspection_posture": "read_only_no_import",
    }:
        raise VerificationError("GoatCitadel release baseline drift")
    goat_head = comparison["goatcitadel_local_head_observation"]
    _require_keys(
        goat_head,
        {"commit_ref", "package_version", "score_posture"},
        "GoatCitadel local observation",
    )
    if goat_head != {
        "commit_ref": "git-sha:91775e6905c8ca6c5083444f64eb3457b2d0aaa0",
        "package_version": "0.1.0-rc.1",
        "score_posture": "not_scored_different_target",
    }:
        raise VerificationError("GoatCitadel local head observation drift")
    if not GIT_SHA_RE.fullmatch(goat_head["commit_ref"]) or not SEMVER_RE.fullmatch(
        goat_head["package_version"]
    ):
        raise VerificationError("GoatCitadel local head ref or version is invalid")

    if data["scoring"] != {
        "minimum": 0,
        "maximum": 10,
        "weight_total": 124,
        "formula": "round_half_up(sum(score*weight)/124*10,1)",
    }:
        raise VerificationError("scoring contract drift")
    components = data["components"]
    if not isinstance(components, list) or len(components) != 16:
        raise VerificationError("exactly sixteen components are required")
    taxonomy = tuple(
        (row.get("component_id"), row.get("label"), row.get("phase_owner"))
        for row in components
    )
    if taxonomy != EXPECTED_COMPONENTS:
        raise VerificationError("component taxonomy drift")
    if tuple(row.get("weight") for row in components) != EXPECTED_WEIGHTS:
        raise VerificationError("component weights drift")
    baseline_by_id = {row["component_id"]: row for row in baseline_data["components"]}
    for row in components:
        _require_keys(row, COMPONENT_KEYS, f"component {row.get('component_id')}")
        expected_before = baseline_by_id[row["component_id"]]["uaa"]["score"]
        if row["before_score"] != expected_before:
            raise VerificationError("component before score drift")
        for system in ("uaa", "goatcitadel"):
            assessment = row[system]
            _require_keys(assessment, ASSESSMENT_KEYS, f"{system} assessment")
            score = assessment["score"]
            if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 10:
                raise VerificationError("component score is invalid")
            if assessment["status"] not in SAFE_STATUSES:
                raise VerificationError("component status is invalid")
            if assessment["confidence"] not in {"high", "medium", "low"}:
                raise VerificationError("component confidence is invalid")
            if not assessment["gap"] or not assessment["recommendation"]:
                raise VerificationError("gap and recommendation are required")
            _validate_safe_free_text(assessment["gap"], f"{system} gap")
            _validate_safe_free_text(
                assessment["recommendation"], f"{system} recommendation"
            )
            refs = assessment["evidence_refs"]
            if not isinstance(refs, list) or not refs:
                raise VerificationError("evidence refs are required")
            paths = [_validate_ref(ref, system=system) for ref in refs]
            required_refs = set(EXPECTED_COMPONENT_EVIDENCE[row["component_id"]][system])
            if not required_refs.issubset(refs):
                raise VerificationError(
                    f"{row['component_id']} {system} canonical evidence binding drift"
                )
            if system == "uaa" and score > row["before_score"]:
                if not any(path.startswith("src/") for path in paths):
                    raise VerificationError("score increase requires implementation evidence")
                if not any(path.startswith("tests/") for path in paths):
                    raise VerificationError("score increase requires test evidence")
                if not any(
                    path.startswith("apps/control-center/") or path.startswith("scripts/")
                    for path in paths
                ):
                    raise VerificationError("score increase requires operator evidence")

    totals = data["weighted_totals"]
    _require_keys(totals, {"uaa", "goatcitadel"}, "weighted totals")
    for system in ("uaa", "goatcitadel"):
        if Decimal(str(totals[system])) != _weighted_total(components, system):
            raise VerificationError(f"{system} weighted total drift")
    if totals != {"uaa": 82.8, "goatcitadel": 84.3}:
        raise VerificationError("final totals drift")

    scenario_data = verify_scenarios(SCENARIOS)
    scenario_binding = data["scenario_results"]
    _require_keys(
        scenario_binding,
        {"artifact_ref", "artifact_sha256", "scenario_count", "passed_count", "blocked_count"},
        "scenario binding",
    )
    expected_scenario_binding = {
        "artifact_ref": "repo-ref:uaa:docs/benchmarks/runtime_capability_foundation/phase09_scenario_results.json",
        "artifact_sha256": _sha256(SCENARIOS),
        "scenario_count": scenario_data["scenario_count"],
        "passed_count": sum(row["status"] == "passed" for row in scenario_data["scenarios"]),
        "blocked_count": sum(row["status"] == "blocked" for row in scenario_data["scenarios"]),
    }
    if scenario_binding != expected_scenario_binding:
        raise VerificationError("scenario result binding drift")

    repair_passes = data["repair_passes"]
    if not isinstance(repair_passes, list) or len(repair_passes) > 2:
        raise VerificationError("repair passes must remain at or below two")
    for repair in repair_passes:
        _require_keys(
            repair,
            {"repair_pass_ref", "status", "safe_summary", "evidence_refs"},
            "repair pass",
        )
        if repair["status"] != "completed" or not repair["safe_summary"]:
            raise VerificationError("repair pass is incomplete")
        if not OPAQUE_REPAIR_REF_RE.fullmatch(repair["repair_pass_ref"]):
            raise VerificationError("repair pass ref is invalid")
        _validate_safe_free_text(repair["safe_summary"], "repair safe summary")
        for ref in repair["evidence_refs"]:
            _validate_ref(ref, system="uaa")

    unresolved = data["unresolved_items"]
    if not isinstance(unresolved, list) or not unresolved:
        raise VerificationError("unresolved items must be explicit")
    for item in unresolved:
        _require_keys(
            item,
            {"item_ref", "classification", "safe_summary", "evidence_refs"},
            "unresolved item",
        )
        if item["classification"] not in TERMINAL_CLASSIFICATIONS:
            raise VerificationError("unresolved classification is invalid")
        if not OPAQUE_UNRESOLVED_REF_RE.fullmatch(item["item_ref"]):
            raise VerificationError("unresolved item ref is invalid")
        if not item["safe_summary"]:
            raise VerificationError("unresolved safe summary is required")
        _validate_safe_free_text(item["safe_summary"], "unresolved safe summary")
        for ref in item["evidence_refs"]:
            _validate_ref(ref, system="uaa")
    if data["redaction"] != REDACTION:
        raise VerificationError("final redaction contract drift")


def verify_report(
    data: dict[str, Any],
    report_path: Path = FINAL_REPORT,
    scorecard_path: Path = FINAL_SCORECARD,
) -> None:
    try:
        text = _read_bounded_bytes(report_path).decode("utf-8")
    except (UnicodeDecodeError, VerificationError) as exc:
        raise VerificationError("final report is missing") from exc
    _validate_safe_report_text(text)
    required = {
        f"Final scorecard hash:\n`{_sha256(scorecard_path)}`",
        f"Scenario result hash:\n`{_sha256(SCENARIOS)}`",
        "| 1 | GoatCitadel v1.0.0 | 84.3 |",
        "| 2 | UAA v0.104.0 after Phases 01-08 | 82.8 |",
        "**Overall stronger today:** GoatCitadel v1.0.0",
        "Exactly twelve scenarios ran.",
        "optional and is not activated by this report",
        "91775e6905c8ca6c5083444f64eb3457b2d0aaa0",
        "0.1.0-rc.1",
    }
    required.update(f"## {index}." for index in range(1, 14))
    required.update(item["classification"] for item in data["unresolved_items"])
    for row in data["components"]:
        required.add(
            f"| {row['label']} | {row['weight']} | {row['before_score']:.1f} | "
            f"{row['uaa']['score']:.1f} | {row['goatcitadel']['score']:.1f} |"
        )
    missing = sorted(item for item in required if item not in text)
    if missing:
        raise VerificationError(f"final report drift: missing {missing[0]}")
    for stale in (
        "mapped_not_run",
        "stop after phase 01",
        "recursively generated follow-on",
        "final 30-day plan",
    ):
        if stale in text.lower():
            raise VerificationError(f"final report contains stale text: {stale}")


def verify(
    path: Path = FINAL_SCORECARD,
    report_path: Path = FINAL_REPORT,
) -> dict[str, Any]:
    data = _read_bounded_json(path)
    verify_data(data)
    verify_report(data, report_path, path)
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scorecard", type=Path, default=FINAL_SCORECARD)
    parser.add_argument("--report", type=Path, default=FINAL_REPORT)
    args = parser.parse_args(argv)
    try:
        data = verify(args.scorecard, args.report)
    except VerificationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        "UAA Phase 09 final scorecard verified: "
        f"UAA={data['weighted_totals']['uaa']:.1f}; "
        f"GoatCitadel={data['weighted_totals']['goatcitadel']:.1f}; finite stop"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
