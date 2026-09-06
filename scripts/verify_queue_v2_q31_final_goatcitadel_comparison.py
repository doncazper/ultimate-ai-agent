#!/usr/bin/env python3
"""Verify the finite, redacted Queue V2 Q31 comparison packet."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.planning.validation import (
    RAW_LOCAL_PATH_RE,
    SAFE_REF_RE,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT = (
    ROOT / "docs" / "benchmarks" / "q31_goat_maturity_input_20260906.json"
)
DEFAULT_REPORT = (
    ROOT / "docs" / "benchmarks" / "Q31_FINAL_GOATCITADEL_COMPARISON_20260906.md"
)
DEFAULT_GOAT_MANIFEST = (
    ROOT / "docs" / "benchmarks" / "q31_goat_evidence_manifest_20260906.json"
)
SCHEMA_VERSION = "goat-comparison-maturity.v2"
COMPARISON_REF = "queue-v2-q31-final-goatcitadel-comparison-20260906"
REPORT_REF_PREFIX = "report-ref:q31:sha256:"
REPORT_SHA256 = "42f101cf10998d0f63d386ee7958ff0ebb69853cbe94ce1e01bd43722fd9a47f"
GOAT_MANIFEST_SCHEMA_VERSION = "goat-evidence-manifest.v1"
GOAT_MANIFEST_REF_PREFIX = "repository-manifest-ref:q31:goat-evidence@sha256:"
GOAT_MANIFEST_SHA256 = (
    "11788e88b398f1664ab6897f10f0c0c1640e66dcfc20d3b8b0726ffc6e32acf0"
)
SCORER_PATH = Path(__file__).resolve()
SCORER_REF_PREFIX = (
    f"repository-scorer-ref:{SCHEMA_VERSION}:"
    "scripts/verify_queue_v2_q31_final_goatcitadel_comparison.py@sha256:"
)
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
    "/home/",
    "/private/tmp/",
    "file://",
    "sess_",
    "api_key=",
    "password=",
)
PROHIBITED_DURABLE_KEYS = {
    "credentialmaterial",
    "credentialpayload",
    "credentialtext",
    "credentialvalue",
    "environmentdump",
    "environmentvariables",
    "hostname",
    "localpath",
    "logtext",
    "promptbody",
    "promptcontent",
    "prompttext",
    "providerexchange",
    "providerpayload",
    "rawlog",
    "rawprompt",
    "rawresponse",
    "responsebody",
    "responsecontent",
    "responsetext",
    "serialnumber",
    "username",
}
SENSITIVE_KEY_FAMILIES = (
    "raw",
    "prompt",
    "response",
    "result",
    "page",
    "message",
    "body",
    "content",
    "payload",
    "log",
    "path",
    "environment",
    "username",
    "hostname",
    "apikey",
    "authkey",
    "authtoken",
    "accesskey",
    "accesstoken",
    "refreshtoken",
    "idtoken",
    "privatekey",
    "clientsecret",
    "authorization",
    "cookie",
    "password",
    "secret",
    "credential",
    "token",
)
ALLOWED_SENSITIVE_POSTURE_KEYS = {
    "rawmodelintelligencescored",
    "result",
    "weightedtotalraw",
}
TOP_LEVEL_KEYS = {
    "schema_version",
    "comparison_ref",
    "report_ref",
    "goat_evidence_manifest_ref",
    "comparison_date",
    "authority_granted",
    "baselines",
    "method",
    "expected_scores",
    "common_evidence_refs",
    "direct_observations",
    "unexercised_observation_dimensions",
    "systems",
    "reciprocal_learning",
    "residual_gap_routes",
    "blocked_follow_up",
}
BASELINE_KEYS = {
    "uaa": {
        "commit_ref",
        "branch",
        "package_version",
        "worktree_status",
        "release_note",
    },
    "goatcitadel": {
        "commit_ref",
        "branch",
        "package_version",
        "mission_control_version",
        "worktree_status",
        "release_note",
    },
}
EXPECTED_SCORES_KEYS = {"scorer_ref", "systems"}
EXPECTED_SYSTEM_SCORE_KEYS = {
    "weighted_total_raw",
    "weighted_total_reported",
    "band",
    "components",
}
AUTHORITY_KEYS = {
    "provider_or_model_calls",
    "competitor_code_import",
    "runtime_mutation",
    "production_claim",
    "automatic_gap_fix",
}
METHOD_KEYS = {
    "prior_score_policy",
    "independent_validation",
    "controlled_model_task_trials",
    "product_experience",
    "winner_threshold_points",
    "raw_model_intelligence_scored",
}
COMPONENT_KEYS = {
    "weight",
    "status",
    "validation_posture",
    "operator_facing",
    "evidence_kind",
    "gates",
    "evidence_refs",
    "acceptance_evidence_refs",
    "breadth_evidence_refs",
    "repeatability_evidence_refs",
    "contradiction_refs",
    "critical_failure_refs",
    "blocker_refs",
    "representative_scope_count",
}
EXPECTED_OBSERVATIONS = {
    ("uaa", "scenario-ref:q31:clean-start-no-provider"): "blocked",
    ("uaa", "scenario-ref:q31:surface-discovery"): "partial",
    ("uaa", "scenario-ref:q31:responsive-390x844"): "partial",
    ("goatcitadel", "scenario-ref:q31:clean-start-no-provider"): "implemented",
    ("goatcitadel", "scenario-ref:q31:draft-thread-switch-refresh"): "partial",
    ("goatcitadel", "scenario-ref:q31:responsive-390x844"): "implemented",
}
EXPECTED_GAP_ROUTES = {
    (
        "finding-ref:q31:uaa:clean-start-chat-gated",
        "Q33",
        "Q31",
        "P0",
    ),
    (
        "finding-ref:q31:uaa:setup-degrades-after-readable-api-responses",
        "Q33",
        "Q31",
        "P0",
    ),
    (
        "finding-ref:q31:uaa:mobile-runtime-card-overlap",
        "Q36",
        "Q31",
        "P1",
    ),
    (
        "finding-ref:q31:uaa:ordinary-chat-primary-nav-discoverability",
        "Q33",
        "Q31",
        "P1",
    ),
}
EXPECTED_BLOCKED_FOLLOW_UP = {
    "finding_ref": "finding-ref:q31:controlled-model-task-performance-not-measured",
    "owner": None,
    "disposition": "blocked_pending_separate_queue_admission",
    "guardrail_ref": "guardrail-ref:q31:no-provider-or-model-call-authority",
}
UAA_REF = re.compile(r"^repo-ref:uaa@([0-9a-f]{8}|[0-9a-f]{40}):([^#]+)$")
GOAT_REF = re.compile(r"^repo-ref:goat@([0-9a-f]{8}|[0-9a-f]{40}):([^#]+)$")
REVISION_SUFFIX = re.compile(r"@(?:git-sha:)?([0-9a-f]{8}|[0-9a-f]{40})$")
CONTENT_ADDRESSED_REF = re.compile(r"^[-A-Za-z0-9_./:@]+:sha256:[0-9a-f]{64}$")
EXPECTED_OBSERVATIONS_DIGEST = (
    "c590e82d9dfebf8d6e7ad340c11f5a1b5064ccceeec80bae2f611413b6fc6a57"
)
EXPECTED_BASELINES_DIGEST = (
    "c2b3f8942b45bad49ce40b9507d0530e53e4552b3eaf96e92efe8f2ae60b3f1c"
)
EXPECTED_SYSTEMS_DIGEST = (
    "0ca47818f73357c229969bb767ff4190b6ca034ffcad64255340f2ff3b6e1e99"
)
EXPECTED_UNEXERCISED_DIMENSIONS = {
    "approvals",
    "artifacts",
    "attachments_or_context_selection",
    "citations",
    "errors",
    "streaming",
    "cancel_retry",
    "interruption",
    "steering",
    "resumption",
    "restart",
    "surface_transitions",
    "terminal_state_clarity",
    "uncertainty",
    "accessibility",
    "steps_and_time_to_useful_outcome",
}
EXPECTED_UNEXERCISED_DIMENSIONS_DIGEST = (
    "b60f90eb8ea2deb046ba1f65df14467a482aaed21bdb4b3aa6c93dd851643682"
)
EXPECTED_RECIPROCAL_LEARNING_DIGEST = (
    "235aa4c5642cf2ff6e392cfc6bfbf61860aace2f394e7e659d4ba23a893cbe93"
)
QUEUE_TRUTH_SENTENCE = (
    "Queue truth: this is the final comparison candidate; Q31 remains pending "
    "until protected merge, post-merge qualification, and the Queue V2 terminal "
    "receipt complete. Q32 remains blocked until that terminal receipt exists."
)


class VerificationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def _safe_refs(
    component: dict[str, Any], field: str, *, required: bool = False
) -> list[str]:
    value = component.get(field, [])
    _require(
        isinstance(value, list)
        and all(isinstance(item, str) and item.strip() for item in value),
        f"{field} must contain safe string refs",
    )
    if required:
        _require(bool(value), f"{field} cannot be empty")
    return value


def _baseline_sha(system_name: str) -> str:
    return BASELINES[system_name].removeprefix("git-sha:")


def _validate_revision_bound_ref(
    ref: str,
    system_name: str,
    *,
    goat_manifest_paths: set[str],
) -> None:
    expected_sha = _baseline_sha(system_name)
    repo_match = UAA_REF.match(ref) if system_name == "uaa" else GOAT_REF.match(ref)
    expected_prefix = f"repo-ref:{system_name if system_name == 'uaa' else 'goat'}@"
    if ref.startswith("repo-ref:"):
        _require(
            ref.startswith(expected_prefix),
            f"{system_name}: repository evidence owner drift",
        )
        _require(
            repo_match is not None, f"{system_name}: invalid repository evidence ref"
        )
        assert repo_match is not None
        claimed_sha = repo_match.group(1)
        _require(
            claimed_sha == expected_sha or claimed_sha == expected_sha[:8],
            f"{system_name}: repository evidence baseline drift",
        )
        path = repo_match.group(2)
        _require(
            not Path(path).is_absolute() and ".." not in Path(path).parts,
            "unsafe repository evidence path",
        )
        if system_name == "uaa":
            exists = subprocess.run(
                ["git", "cat-file", "-e", f"{expected_sha}:{path}"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            _require(
                exists.returncode == 0, f"missing UAA evidence file at baseline: {path}"
            )
        else:
            _require(
                path in goat_manifest_paths,
                f"missing GoatCitadel evidence file in manifest: {path}",
            )
        return
    if CONTENT_ADDRESSED_REF.fullmatch(ref) is not None:
        return
    revision_match = REVISION_SUFFIX.search(ref)
    _require(
        revision_match is not None,
        f"{system_name}: evidence ref lacks provenance",
    )
    assert revision_match is not None
    claimed_sha = revision_match.group(1)
    _require(
        claimed_sha == expected_sha or claimed_sha == expected_sha[:8],
        f"{system_name}: evidence ref baseline drift",
    )


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _reject_duplicate_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _loads_strict_json(text: str) -> Any:
    return json.loads(text, object_pairs_hook=_reject_duplicate_object_pairs)


def _validate_goat_manifest(manifest: Any) -> set[str]:
    _require(
        isinstance(manifest, dict)
        and set(manifest) == {"schema_version", "baseline_commit_ref", "files"},
        "GoatCitadel evidence manifest shape drift",
    )
    _require(
        manifest["schema_version"] == GOAT_MANIFEST_SCHEMA_VERSION,
        "GoatCitadel evidence manifest schema drift",
    )
    _require(
        manifest["baseline_commit_ref"] == BASELINES["goatcitadel"],
        "GoatCitadel evidence manifest baseline drift",
    )
    files = manifest["files"]
    _require(
        isinstance(files, list) and bool(files),
        "GoatCitadel evidence manifest is empty",
    )
    paths: list[str] = []
    for item in files:
        _require(
            isinstance(item, dict) and set(item) == {"path", "sha256"},
            "GoatCitadel evidence manifest entry shape drift",
        )
        path = item["path"]
        digest = item["sha256"]
        _require(
            isinstance(path, str)
            and bool(path)
            and not Path(path).is_absolute()
            and ".." not in Path(path).parts,
            "unsafe GoatCitadel evidence manifest path",
        )
        _require(
            isinstance(digest, str)
            and re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
            "invalid GoatCitadel evidence manifest digest",
        )
        paths.append(path)
    _require(paths == sorted(set(paths)), "GoatCitadel evidence manifest path drift")
    _require(
        _canonical_digest(manifest) == GOAT_MANIFEST_SHA256,
        "GoatCitadel evidence manifest digest drift",
    )
    return set(paths)


def _validate_safe_ref(ref: str, field_name: str) -> None:
    _require(
        SAFE_REF_RE.fullmatch(ref) is not None,
        f"{field_name} must be a structured safe ref",
    )
    _require(
        RAW_LOCAL_PATH_RE.search(ref) is None,
        f"{field_name} contains an unsafe path",
    )
    _require(
        not contains_secret_like(ref) and not contains_obvious_secret(ref),
        f"{field_name} contains secret-like content",
    )


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
    if (
        component.get("prior_verified_score") is not None
        and component["validation_posture"] != "accepted"
    ):
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
            sensitive_family = any(
                family in normalized for family in SENSITIVE_KEY_FAMILIES
            )
            _require(
                normalized not in PROHIBITED_DURABLE_KEYS
                and (
                    normalized in ALLOWED_SENSITIVE_POSTURE_KEYS or not sensitive_family
                ),
                f"unsafe durable field: {key}",
            )
            _walk_for_unsafe_text(child)
    elif isinstance(value, list):
        for child in value:
            _walk_for_unsafe_text(child)
    elif isinstance(value, str):
        _require(
            not any(fragment in value for fragment in PROHIBITED_TEXT),
            "unsafe durable text",
        )
        _require(RAW_LOCAL_PATH_RE.search(value) is None, "unsafe durable text")
        _require(
            re.search(r"\bsk-[A-Za-z0-9]{8,}", value) is None, "unsafe durable text"
        )


def _validate_report(data: dict[str, Any], report: str) -> None:
    for section in REQUIRED_REPORT_SECTIONS:
        _require(section in report, f"report section missing: {section}")
    scores = data["expected_scores"]["systems"]
    uaa_score = scores["uaa"]["weighted_total_reported"]
    goat_score = scores["goatcitadel"]["weighted_total_reported"]
    expected_projection = (
        f"Report binding: UAA `{BASELINES['uaa']}`; GoatCitadel "
        f"`{BASELINES['goatcitadel']}`; scores `UAA={uaa_score}` and "
        f"`GoatCitadel={goat_score}`; independent validation `not_performed`; "
        "controlled model task trials `not_measured`; residual owners `Q33,Q36`; "
        "Q31 repair authority `denied`."
    )
    _require(report.count(expected_projection) == 1, "report projection drift")
    _require(
        f"The evidence-gated repository maturity score is **GoatCitadel {goat_score}, UAA {uaa_score}**."
        in report,
        "report executive score drift",
    )
    raw_gap = (
        scores["goatcitadel"]["weighted_total_raw"]
        - scores["uaa"]["weighted_total_raw"]
    )
    _require(
        report.count(f"({raw_gap:.4f} raw)") == 1,
        "report raw score delta drift",
    )
    _require(
        f"GoatCitadel has a slight current repository-maturity lead, **{goat_score} to {uaa_score}**"
        in report,
        "report final score drift",
    )
    _require(
        report.count("No Q31 finding authorizes its own repair.") == 1,
        "report authority posture drift",
    )
    _require(
        report.lower().count("authorizes its own repair") == 1,
        "report contains contradictory repair authority",
    )
    report_shas = set(re.findall(r"git-sha:[0-9a-f]{40}", report))
    _require(report_shas == set(BASELINES.values()), "report baseline binding drift")
    _require(
        "not a controlled" in report.lower(),
        "report must preserve non-empirical posture",
    )
    _require(
        not any(fragment in report for fragment in PROHIBITED_TEXT),
        "unsafe report text",
    )
    _require(RAW_LOCAL_PATH_RE.search(report) is None, "unsafe report text")
    _require(
        not contains_secret_like(report) and not contains_obvious_secret(report),
        "unsafe report text",
    )
    _require(
        report.count(QUEUE_TRUTH_SENTENCE) == 1,
        "report queue truth drift",
    )
    report_digest = hashlib.sha256(report.encode()).hexdigest()
    _require(report_digest == REPORT_SHA256, "canonical report digest drift")
    _require(
        data.get("report_ref") == f"{REPORT_REF_PREFIX}{REPORT_SHA256}",
        "report ref drift",
    )


def verify_data(
    data: dict[str, Any],
    report: str,
    goat_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _require(isinstance(data, dict), "top-level ledger must be an object")
    _require(data.get("schema_version") == SCHEMA_VERSION, "schema version drift")
    _require(data.get("comparison_ref") == COMPARISON_REF, "comparison ref drift")
    _require(data.get("comparison_date") == "2026-09-06", "comparison date drift")
    _walk_for_unsafe_text(data)
    _require(set(data) == TOP_LEVEL_KEYS, "top-level ledger schema drift")
    if goat_manifest is None:
        goat_manifest = _loads_strict_json(
            DEFAULT_GOAT_MANIFEST.read_text(encoding="utf-8")
        )
    goat_manifest_paths = _validate_goat_manifest(goat_manifest)
    _require(
        data.get("goat_evidence_manifest_ref")
        == f"{GOAT_MANIFEST_REF_PREFIX}{GOAT_MANIFEST_SHA256}",
        "GoatCitadel evidence manifest ref drift",
    )
    baselines = data.get("baselines")
    _require(
        isinstance(baselines, dict) and set(baselines) == set(BASELINE_KEYS),
        "baseline inventory drift",
    )
    for system_name, expected_keys in BASELINE_KEYS.items():
        _require(
            isinstance(baselines[system_name], dict)
            and set(baselines[system_name]) == expected_keys,
            f"{system_name}: baseline shape drift",
        )
    _require(
        baselines["uaa"].get("commit_ref") == BASELINES["uaa"],
        "UAA baseline drift",
    )
    _require(
        baselines["goatcitadel"].get("commit_ref") == BASELINES["goatcitadel"],
        "GoatCitadel baseline drift",
    )
    _require(
        _canonical_digest(baselines) == EXPECTED_BASELINES_DIGEST,
        "canonical baseline metadata drift",
    )
    authority = data.get("authority_granted")
    _require(
        isinstance(authority, dict) and set(authority) == AUTHORITY_KEYS,
        "authority denial inventory drift",
    )
    _require(
        all(type(value) is bool and value is False for value in authority.values()),
        "comparison cannot grant authority",
    )
    method = data.get("method", {})
    _require(
        isinstance(method, dict) and set(method) == METHOD_KEYS,
        "method inventory drift",
    )
    _require(
        method.get("prior_score_policy")
        == "not_carried_forward_due_to_rubric_discontinuity",
        "prior score policy drift",
    )
    _require(
        method.get("independent_validation") == "not_performed",
        "independent validation posture drift",
    )
    _require(
        method.get("controlled_model_task_trials") == "not_measured",
        "controlled task posture drift",
    )
    _require(
        method.get("product_experience") == "single_evaluator_formative_only",
        "product experience posture drift",
    )
    _require(
        method.get("raw_model_intelligence_scored") is False,
        "raw model intelligence cannot be scored",
    )
    _require(
        type(method.get("winner_threshold_points")) is int
        and method["winner_threshold_points"] == 3,
        "winner threshold drift",
    )

    systems = data.get("systems")
    _require(
        isinstance(systems, dict) and set(systems) == set(BASELINES),
        "system inventory drift",
    )
    common_refs = data.get("common_evidence_refs")
    _require(
        isinstance(common_refs, dict) and common_refs, "common evidence refs missing"
    )
    for ref_name, ref in common_refs.items():
        _require(
            isinstance(ref_name, str) and isinstance(ref, str),
            "common evidence ref shape drift",
        )
        _validate_safe_ref(ref, f"common_evidence_refs/{ref_name}")
        if ref_name.startswith("uaa_"):
            _validate_revision_bound_ref(
                ref, "uaa", goat_manifest_paths=goat_manifest_paths
            )
        elif ref_name.startswith("goat_"):
            _validate_revision_bound_ref(
                ref, "goatcitadel", goat_manifest_paths=goat_manifest_paths
            )
        else:
            raise VerificationError(f"unowned common evidence ref: {ref_name}")
    expected_scores = data.get("expected_scores", {})
    _require(
        isinstance(expected_scores, dict)
        and set(expected_scores) == EXPECTED_SCORES_KEYS,
        "expected score schema drift",
    )
    scorer_digest = hashlib.sha256(SCORER_PATH.read_bytes()).hexdigest()
    _require(
        expected_scores.get("scorer_ref") == f"{SCORER_REF_PREFIX}{scorer_digest}",
        "scorer ref drift",
    )
    expected = expected_scores.get("systems")
    _require(
        isinstance(expected, dict) and set(expected) == set(BASELINES),
        "expected score inventory drift",
    )
    for system_name, components in systems.items():
        _require(
            isinstance(expected[system_name], dict)
            and set(expected[system_name]) == EXPECTED_SYSTEM_SCORE_KEYS,
            f"{system_name}: expected score shape drift",
        )
        _require(
            isinstance(expected[system_name]["components"], dict)
            and set(expected[system_name]["components"]) == set(WEIGHTS),
            f"{system_name}: expected component inventory drift",
        )
        _require(
            isinstance(components, dict) and set(components) == set(WEIGHTS),
            f"{system_name}: component inventory drift",
        )
        weighted_points = 0
        for component_name, component in components.items():
            _require(
                isinstance(component, dict) and set(component) == COMPONENT_KEYS,
                f"{system_name}/{component_name}: component shape drift",
            )
            _require(
                component.get("weight") == WEIGHTS[component_name],
                f"{system_name}/{component_name}: weight drift",
            )
            _require(
                component.get("status") in STATUSES,
                f"{system_name}/{component_name}: invalid status",
            )
            _require(
                component.get("validation_posture") in VALIDATION_POSTURES,
                f"{system_name}/{component_name}: invalid validation posture",
            )
            _require(
                isinstance(component.get("operator_facing"), bool),
                f"{system_name}/{component_name}: operator flag drift",
            )
            _require(
                component.get("evidence_kind") in {"code", "runtime"},
                f"{system_name}/{component_name}: evidence kind drift",
            )
            _require(
                type(component.get("representative_scope_count")) is int
                and component["representative_scope_count"] >= 0,
                f"{system_name}/{component_name}: representative scope drift",
            )
            gates = component.get("gates")
            _require(
                isinstance(gates, dict) and set(gates) == set(GATE_MAXIMA),
                f"{system_name}/{component_name}: gate inventory drift",
            )
            for gate_name, maximum in GATE_MAXIMA.items():
                gate = gates[gate_name]
                _require(
                    type(gate) is int and 0 <= gate <= maximum,
                    f"{system_name}/{component_name}/{gate_name}: invalid gate",
                )
            _require(
                gates["independent_validation"] == 0,
                f"{system_name}/{component_name}: independent validation not available",
            )
            _require(
                component["validation_posture"] != "accepted",
                f"{system_name}/{component_name}: self-evidence cannot be accepted",
            )
            _require(
                not _safe_refs(component, "acceptance_evidence_refs"),
                f"{system_name}/{component_name}: acceptance refs not authorized",
            )
            refs = _safe_refs(component, "evidence_refs", required=True)
            for field in (
                "breadth_evidence_refs",
                "repeatability_evidence_refs",
                "contradiction_refs",
                "critical_failure_refs",
                "blocker_refs",
            ):
                _safe_refs(component, field)
            all_refs = refs.copy()
            for field in (
                "breadth_evidence_refs",
                "repeatability_evidence_refs",
                "contradiction_refs",
                "critical_failure_refs",
                "blocker_refs",
            ):
                all_refs.extend(_safe_refs(component, field))
            for ref in all_refs:
                _validate_safe_ref(ref, f"{system_name}/{component_name}/evidence_ref")
                _validate_revision_bound_ref(
                    ref,
                    system_name,
                    goat_manifest_paths=goat_manifest_paths,
                )
            score = _component_score(component)
            _require(
                expected[system_name]["components"].get(component_name) == score,
                f"{system_name}/{component_name}: expected score drift",
            )
            weighted_points += score * WEIGHTS[component_name]
        raw_total = round(weighted_points / sum(WEIGHTS.values()) * 10, 4)
        reported = int(raw_total + 0.5)
        _require(
            expected[system_name].get("weighted_total_raw") == raw_total,
            f"{system_name}: raw weighted total drift",
        )
        _require(
            expected[system_name].get("weighted_total_reported") == reported,
            f"{system_name}: reported weighted total drift",
        )
        _require(
            expected[system_name].get("band") == _band(reported),
            f"{system_name}: maturity band drift",
        )
    _require(
        _canonical_digest(systems) == EXPECTED_SYSTEMS_DIGEST,
        "canonical component score inputs drift",
    )

    observations = data.get("direct_observations")
    _require(isinstance(observations, list), "direct observation inventory incomplete")
    observed: dict[tuple[str, str], str] = {}
    for item in observations:
        _require(
            isinstance(item, dict)
            and set(item)
            == {"system", "scenario_ref", "status", "result", "evidence_refs"},
            "direct observation shape drift",
        )
        _require(item["system"] in BASELINES, "unknown direct observation system")
        identity = (item["system"], item["scenario_ref"])
        _require(identity not in observed, "duplicate direct observation identity")
        observed[identity] = item["status"]
        refs = _safe_refs(item, "evidence_refs", required=True)
        for ref in refs:
            _validate_safe_ref(ref, "direct_observation/evidence_ref")
            _validate_revision_bound_ref(
                ref,
                item["system"],
                goat_manifest_paths=goat_manifest_paths,
            )
    _require(observed == EXPECTED_OBSERVATIONS, "direct observation inventory drift")
    _require(
        _canonical_digest(observations) == EXPECTED_OBSERVATIONS_DIGEST,
        "direct observation evidence binding drift",
    )
    unexercised = data.get("unexercised_observation_dimensions")
    _require(
        isinstance(unexercised, list)
        and len(unexercised) == len(EXPECTED_UNEXERCISED_DIMENSIONS),
        "unexercised observation dimension inventory drift",
    )
    observed_dimensions: set[str] = set()
    for item in unexercised:
        _require(
            isinstance(item, dict)
            and set(item) == {"dimension", "uaa", "goatcitadel", "reason"},
            "unexercised observation dimension shape drift",
        )
        dimension = item["dimension"]
        _require(
            isinstance(dimension, str) and dimension not in observed_dimensions,
            "duplicate unexercised observation dimension",
        )
        observed_dimensions.add(dimension)
        _require(
            item["uaa"] == "not_measured" and item["goatcitadel"] == "not_measured",
            "unexercised observation status drift",
        )
        _require(
            isinstance(item["reason"], str) and bool(item["reason"].strip()),
            "unexercised observation reason missing",
        )
    _require(
        observed_dimensions == EXPECTED_UNEXERCISED_DIMENSIONS,
        "unexercised observation dimension inventory drift",
    )
    _require(
        _canonical_digest(unexercised) == EXPECTED_UNEXERCISED_DIMENSIONS_DIGEST,
        "unexercised observation evidence binding drift",
    )

    routes = data.get("residual_gap_routes")
    _require(isinstance(routes, list), "residual gap routes missing")
    route_inventory: set[tuple[str, str, str, str]] = set()
    for item in routes:
        _require(
            isinstance(item, dict)
            and set(item) == {"finding_ref", "owner", "dependency", "priority"},
            "residual gap route shape drift",
        )
        route = (
            item["finding_ref"],
            item["owner"],
            item["dependency"],
            item["priority"],
        )
        _require(route not in route_inventory, "duplicate residual gap route")
        route_inventory.add(route)
    _require(
        route_inventory == EXPECTED_GAP_ROUTES, "residual gap route inventory drift"
    )
    _require(
        data.get("blocked_follow_up") == EXPECTED_BLOCKED_FOLLOW_UP,
        "blocked follow-up posture drift",
    )
    learning = data.get("reciprocal_learning")
    _require(
        isinstance(learning, list) and len(learning) == 7,
        "reciprocal learning ledger incomplete",
    )
    learning_identities: set[tuple[str, str]] = set()
    for item in learning:
        _require(
            isinstance(item, dict)
            and set(item)
            == {
                "direction",
                "pattern",
                "transfer_score",
                "disposition",
                "uaa_owner",
                "exit_test",
            },
            "reciprocal learning entry shape drift",
        )
        _require(
            isinstance(item["pattern"], str) and bool(item["pattern"].strip()),
            "reciprocal learning pattern missing",
        )
        _require(
            type(item["transfer_score"]) is int and 0 <= item["transfer_score"] <= 10,
            "reciprocal learning score drift",
        )
        _require(
            item["uaa_owner"] in {"Q31", "Q33", "Q36", "external_only"},
            "reciprocal learning owner drift",
        )
        _require(
            isinstance(item["exit_test"], str) and bool(item["exit_test"].strip()),
            "reciprocal learning exit test missing",
        )
        identity = (item["direction"], item["pattern"])
        _require(
            identity not in learning_identities, "duplicate reciprocal learning entry"
        )
        learning_identities.add(identity)
    do_not_borrow = [
        item for item in learning if item.get("disposition") == "do_not_borrow"
    ]
    _require(
        len(do_not_borrow) == 1
        and do_not_borrow[0].get("direction") == "bidirectional"
        and do_not_borrow[0].get("transfer_score") == 0,
        "bidirectional do-not-borrow rule drift",
    )
    _require(
        {item.get("direction") for item in learning}
        == {"goatcitadel_to_uaa", "uaa_to_goatcitadel", "bidirectional"},
        "reciprocal direction missing",
    )
    _require(
        all(
            item.get("disposition") in {"adapt", "study_only", "do_not_borrow"}
            for item in learning
        ),
        "invalid transfer disposition",
    )
    _require(
        _canonical_digest(learning) == EXPECTED_RECIPROCAL_LEARNING_DIGEST,
        "reciprocal learning inventory drift",
    )

    _require(
        not contains_secret_like(data) and not contains_obvious_secret(data),
        "unsafe durable text",
    )
    _validate_report(data, report)
    return data


def verify(
    artifact: Path = DEFAULT_ARTIFACT, report_path: Path = DEFAULT_REPORT
) -> dict[str, Any]:
    _require(
        artifact.resolve() == DEFAULT_ARTIFACT.resolve(),
        "artifact path is not canonical",
    )
    _require(
        report_path.resolve() == DEFAULT_REPORT.resolve(),
        "report path is not canonical",
    )
    _require(artifact.stat().st_size <= 250_000, "comparison artifact is unbounded")
    _require(report_path.stat().st_size <= 150_000, "comparison report is unbounded")
    _require(
        DEFAULT_GOAT_MANIFEST.stat().st_size <= 100_000,
        "GoatCitadel evidence manifest is unbounded",
    )
    data = _loads_strict_json(artifact.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    goat_manifest = _loads_strict_json(
        DEFAULT_GOAT_MANIFEST.read_text(encoding="utf-8")
    )
    return verify_data(data, report, goat_manifest)


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
