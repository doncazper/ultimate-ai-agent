#!/usr/bin/env python3
"""Verify the deterministic UAA runtime capability benchmark and scorecard."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK = (
    ROOT / "docs" / "benchmarks" / "runtime_capability_foundation" / "phase00_baseline.json"
)
DEFAULT_REPORT = ROOT / "docs" / "control_center" / "UAA_RUNTIME_CAPABILITY_SCOREBOARD.md"
EXPECTED_SCHEMA = "uaa_runtime_capability_benchmark.v1"
EXPECTED_UAA_COMMIT = "git-sha:5490fe755a7e9004bca38e6da1c2d91f8e2e4a08"
EXPECTED_GOAT_COMMIT = "git-sha:dff26c018b44c394c189c170265a00ab640f1214"
EXPECTED_WEIGHTS = (8, 8, 8, 9, 7, 9, 10, 6, 5, 6, 9, 10, 7, 6, 6, 10)
EXPECTED_COMPONENTS = (
    ("reasoning_task_understanding", "Reasoning and task understanding", "phase_01"),
    ("planning_orchestration", "Planning and orchestration", "phase_02"),
    ("learning_adaptation", "Learning and adaptation", "phase_03"),
    ("memory_context_management", "Memory and context management", "phase_03"),
    ("communication_interaction", "Communication and interaction quality", "phase_08"),
    ("action_tool_calling", "Action and tool calling", "phase_04"),
    ("autonomy_authority", "Autonomy and authority management", "phase_02"),
    ("code_implementation_assistance", "Code and implementation assistance", "phase_04"),
    ("research_web_external", "Research, web, and external information handling", "phase_05"),
    ("model_provider_management", "Model/provider management", "phase_05"),
    ("evidence_audit_observability", "Evidence, audit, and observability", "phase_06"),
    ("safety_security_failure", "Safety, security, and failure handling", "phase_06"),
    ("ux_ai_cockpit", "UX as an AI cockpit", "phase_08"),
    ("cli_api_parity", "CLI/API parity", "phase_08"),
    ("extensibility_ecosystem", "Extensibility and ecosystem", "phase_07"),
    ("productized_agent_loop", "Productized agent loop", "phase_02"),
)
EXPECTED_SCENARIOS = (
    "scenario:ambiguous-intent",
    "scenario:plan-revision",
    "scenario:dag-replay-crash",
    "scenario:approval-expiry",
    "scenario:cancellation-race",
    "scenario:budget-exhaustion-settlement",
    "scenario:exact-tool-idempotency",
    "scenario:sandbox-escape-denial",
    "scenario:memory-correction",
    "scenario:web-citation-injection",
    "scenario:provider-stale-unavailable",
    "scenario:receipt-tamper-surface-parity",
)
EXPECTED_SCENARIO_PHASES = {
    "scenario:ambiguous-intent": ["phase_01"],
    "scenario:plan-revision": ["phase_01"],
    "scenario:dag-replay-crash": ["phase_02"],
    "scenario:approval-expiry": ["phase_02"],
    "scenario:cancellation-race": ["phase_02"],
    "scenario:budget-exhaustion-settlement": ["phase_02"],
    "scenario:exact-tool-idempotency": ["phase_04"],
    "scenario:sandbox-escape-denial": ["phase_04"],
    "scenario:memory-correction": ["phase_03"],
    "scenario:web-citation-injection": ["phase_05"],
    "scenario:provider-stale-unavailable": ["phase_05"],
    "scenario:receipt-tamper-surface-parity": ["phase_06", "phase_08", "phase_09"],
}
EXPECTED_GAP_OWNERS = {
    "gap-ref:typed-intent-and-plan-revision": "phase_01",
    "gap-ref:bounded-founder-loop-completion": "phase_02",
    "gap-ref:governed-context-learning": "phase_03",
    "gap-ref:exact-tool-and-code-lanes": "phase_04",
    "gap-ref:web-research-provider-observability": "phase_05",
    "gap-ref:portable-content-free-evidence": "phase_06",
    "gap-ref:extension-catalog-maturity": "phase_07",
    "gap-ref:operator-cockpit-parity": "phase_08",
    "gap-ref:final-benchmark-and-repair": "phase_09",
}
REQUIRED_PRESERVATION_REFS = {
    "capability-ref:webaccessgateway",
    "capability-ref:web.search.searxng.readonly",
    "capability-ref:web.extract.firecrawl.self_hosted.markdown",
    "capability-ref:web.extract.firecrawl.cloud_free.markdown",
    "capability-ref:web.hybrid.self_host_first.single_fallback",
    "capability-ref:web.hybrid.cloud_budget_credit_reconciliation",
    "capability-ref:web.hybrid.local_services_packaging_configuration",
    "capability-ref:web.hybrid.cli_api_control_center_truth",
    "capability-ref:web.hybrid.activation_and_implementation_plan",
    "capability-ref:typescript.exact.7.0.2",
    "capability-ref:pytest.sharded.timing_aware",
    "capability-ref:verifier.maintainability_refactor",
    "capability-ref:runtime_cli.extracted_modules",
    "capability-ref:mission.failure_management",
    "capability-ref:mission.approval_waits",
    "capability-ref:mission.retries_dead_letters",
    "capability-ref:mission.cancellation_fences",
    "capability-ref:sse.progress_preview.deterministic_replay",
}
REQUIRED_DENIALS = {
    "paid_web_or_provider_use",
    "browser_actions",
    "authenticated_web",
    "cookies",
    "downloads_uploads",
    "external_mutations",
    "broad_host_shell",
    "arbitrary_plugin_import",
    "production_authority",
}
SAFE_STATUSES = {
    "implemented", "partial", "planned", "mock-only", "blocked",
    "deprecated", "contradicted", "unknown",
}
SAFE_CONFIDENCE = {"high", "medium", "low"}
TIMING_STATUSES = {"measured", "external_blocked", "pending_measurement"}
EXPECTED_TIMING_COMMANDS = (
    "command-ref:pytest-shards-tracked-seed",
    "command-ref:frontend-check",
    "command-ref:web-hybrid-focused",
    "command-ref:foundation-gate-report-only",
)
ABSOLUTE_PATH_PATTERN = re.compile(r"(?:^|[\s'\"=(])(?:/[A-Za-z0-9._-]+(?:/[^\s`'\"\]]*)?|[A-Za-z]:\\)")
REPORT_ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?:/Users/|/home/|/private/tmp/|/tmp/|/private/var/|/var/|/etc/|/opt/|/Volumes/|[A-Za-z]:\\)"
)
SECRET_LIKE_VALUE_PATTERN = re.compile(
    r"(?:api[_-]?key|secret|password|credential|access[_-]?token)\s*[:=]",
    re.IGNORECASE,
)
FORBIDDEN_KEYS = {
    "raw_prompt", "raw_response", "raw_result", "raw_page", "raw_log",
    "provider_payload", "credential", "secret", "token", "username", "hostname",
    "environment_dump", "local_path",
}
ALLOWED_SENSITIVE_POSTURE_KEYS = {
    "raw_content_persisted",
    "local_paths_persisted",
}
SENSITIVE_KEY_PATTERN = re.compile(
    r"(?:raw|prompt|response|result|page|message|body|content|payload|log|path|"
    r"credential|secret|token|username|hostname|environment)"
)
UAA_REF_PATTERN = re.compile(r"^repo-ref:uaa:([^#]+)(?:#L\d+(?:-L?\d+)?)?$")
GOAT_REF_PATTERN = re.compile(r"^repo-ref:goatcitadel:v1\.0\.0:([^#]+)(?:#L\d+(?:-L?\d+)?)?$")

TOP_LEVEL_KEYS = {
    "schema_version", "benchmark_ref", "status", "authority_granted", "comparison",
    "scoring", "components", "weighted_totals", "gap_map", "scenarios",
    "preservation_refs", "denied_postures", "timing_snapshot", "redaction",
}
COMPONENT_KEYS = {"component_id", "label", "weight", "phase_owner", "unknown_refs", "uaa", "goatcitadel"}
ASSESSMENT_KEYS = {"score", "status", "confidence", "evidence_refs", "gap_refs", "safe_summary"}


class VerificationError(RuntimeError):
    """Raised when benchmark verification fails."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VerificationError(f"missing benchmark: {path}") from exc
    except json.JSONDecodeError as exc:
        raise VerificationError(f"invalid benchmark json: {exc}") from exc
    if not isinstance(data, dict):
        raise VerificationError("benchmark must be an object")
    return data


def _walk(value: Any, *, key: str | None = None) -> None:
    if key in FORBIDDEN_KEYS or (
        key is not None
        and key not in ALLOWED_SENSITIVE_POSTURE_KEYS
        and SENSITIVE_KEY_PATTERN.search(key.lower())
    ):
        raise VerificationError(f"unsafe durable field: {key}")
    if isinstance(value, dict):
        for child_key, child in value.items():
            _walk(child, key=child_key)
    elif isinstance(value, list):
        for child in value:
            _walk(child)
    elif isinstance(value, str):
        if ABSOLUTE_PATH_PATTERN.search(value):
            raise VerificationError("benchmark contains an absolute local path")
        if SECRET_LIKE_VALUE_PATTERN.search(value):
            raise VerificationError("benchmark contains a secret-like value")


def _require_exact_keys(value: Any, expected: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise VerificationError(f"{label} keys drift")


def _weighted_total(components: list[dict[str, Any]], system: str) -> Decimal:
    numerator = sum(
        Decimal(str(component[system]["score"])) * Decimal(component["weight"])
        for component in components
    )
    return (numerator / Decimal(124) * Decimal(10)).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )


def _benchmark_hash(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _validate_evidence(ref: str) -> None:
    uaa_match = UAA_REF_PATTERN.fullmatch(ref)
    if uaa_match:
        relative = Path(uaa_match.group(1))
        if relative.is_absolute() or ".." in relative.parts or not (ROOT / relative).exists():
            raise VerificationError(f"invalid or missing UAA evidence ref: {ref}")
        return
    goat_match = GOAT_REF_PATTERN.fullmatch(ref)
    if goat_match:
        relative = Path(goat_match.group(1))
        if relative.is_absolute() or ".." in relative.parts:
            raise VerificationError(f"unsafe GoatCitadel evidence ref: {ref}")
        return
    raise VerificationError(f"unsupported evidence ref: {ref}")


def verify_benchmark(data: dict[str, Any], *, allow_pending_timings: bool = False) -> None:
    _walk(data)
    _require_exact_keys(data, TOP_LEVEL_KEYS, "top-level benchmark")
    if data.get("schema_version") != EXPECTED_SCHEMA:
        raise VerificationError("unexpected schema_version")
    if data.get("benchmark_ref") != "benchmark-ref:runtime-capability-foundation:phase00":
        raise VerificationError("unexpected benchmark_ref")
    if data.get("status") != "evidence_backed_baseline":
        raise VerificationError("unexpected benchmark status")
    if data.get("authority_granted") is not False:
        raise VerificationError("benchmark must not grant authority")
    comparison = data.get("comparison", {})
    _require_exact_keys(comparison, {"uaa", "goatcitadel"}, "comparison")
    _require_exact_keys(comparison.get("uaa"), {"version", "commit_ref"}, "UAA baseline")
    if comparison.get("uaa", {}).get("version") != "0.104.0":
        raise VerificationError("unexpected UAA baseline version")
    if comparison.get("uaa", {}).get("commit_ref") != EXPECTED_UAA_COMMIT:
        raise VerificationError("unexpected UAA baseline commit")
    goat = comparison.get("goatcitadel", {})
    _require_exact_keys(
        goat,
        {"version", "tag_ref", "commit_ref", "inspection_posture"},
        "GoatCitadel baseline",
    )
    if goat.get("tag_ref") != "git-tag:v1.0.0" or goat.get("commit_ref") != EXPECTED_GOAT_COMMIT:
        raise VerificationError("unexpected GoatCitadel v1.0.0 baseline")
    if goat.get("inspection_posture") != "read_only_no_import":
        raise VerificationError("GoatCitadel comparison must remain read-only")

    scoring = data.get("scoring", {})
    _require_exact_keys(
        scoring,
        {"minimum", "maximum", "weight_total", "formula", "confidence_values", "status_values"},
        "scoring",
    )
    if scoring.get("minimum") != 0 or scoring.get("maximum") != 10:
        raise VerificationError("scoring bounds drift")
    if scoring.get("formula") != "round_half_up(sum(score*weight)/124*10,1)":
        raise VerificationError("scoring formula drift")
    if scoring.get("weight_total") != 124:
        raise VerificationError("weight_total must be 124")
    if set(scoring.get("status_values", [])) != SAFE_STATUSES:
        raise VerificationError("status_values drift")
    if set(scoring.get("confidence_values", [])) != SAFE_CONFIDENCE:
        raise VerificationError("confidence_values drift")

    components = data.get("components")
    if not isinstance(components, list) or len(components) != 16:
        raise VerificationError("benchmark must contain exactly 16 components")
    observed_components = tuple(
        (component.get("component_id"), component.get("label"), component.get("phase_owner"))
        for component in components
    )
    if observed_components != EXPECTED_COMPONENTS:
        raise VerificationError("component taxonomy/order/ownership drift")
    weights = tuple(component.get("weight") for component in components)
    if weights != EXPECTED_WEIGHTS:
        raise VerificationError(f"component weights drift: {weights!r}")

    observed_gap_refs: set[str] = set()
    expected_gap_owners: dict[str, str] = {}
    for component in components:
        _require_exact_keys(component, COMPONENT_KEYS, f"component {component.get('component_id')}")
        unknown_refs = component.get("unknown_refs")
        if not isinstance(unknown_refs, list) or not unknown_refs or any(
            not isinstance(ref, str) or not ref.startswith("unknown-ref:") for ref in unknown_refs
        ):
            raise VerificationError("component requires explicit safe unknown refs")
        if len(unknown_refs) != len(set(unknown_refs)):
            raise VerificationError("component unknown refs must be unique")
        for system in ("uaa", "goatcitadel"):
            assessment = component.get(system, {})
            _require_exact_keys(assessment, ASSESSMENT_KEYS, f"{system} assessment")
            score = assessment.get("score")
            if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 10:
                raise VerificationError(f"invalid {system} score for {component.get('component_id')}")
            if assessment.get("status") not in SAFE_STATUSES:
                raise VerificationError(f"invalid {system} status")
            if assessment.get("confidence") not in SAFE_CONFIDENCE:
                raise VerificationError(f"invalid {system} confidence")
            evidence = assessment.get("evidence_refs")
            if score > 0 and (not isinstance(evidence, list) or not evidence):
                raise VerificationError(f"positive {system} score requires evidence")
            for ref in evidence or []:
                _validate_evidence(ref)
            gap_refs = assessment.get("gap_refs", [])
            if not isinstance(gap_refs, list):
                raise VerificationError("assessment gap_refs must be a list")
            for gap_ref in gap_refs:
                observed_gap_refs.add(gap_ref)
                expected_gap_owners.setdefault(gap_ref, component["phase_owner"])
                if expected_gap_owners[gap_ref] != component["phase_owner"]:
                    raise VerificationError("one gap cannot have conflicting component owners")

    totals = data.get("weighted_totals", {})
    _require_exact_keys(totals, {"uaa", "goatcitadel"}, "weighted totals")
    for system in ("uaa", "goatcitadel"):
        computed = _weighted_total(components, system)
        if Decimal(str(totals.get(system))) != computed:
            raise VerificationError(
                f"{system} weighted total drift: stored={totals.get(system)!r} computed={computed}"
            )

    gap_map = data.get("gap_map")
    if not isinstance(gap_map, list) or not gap_map:
        raise VerificationError("gap_map must be non-empty")
    mapped = {item.get("gap_ref") for item in gap_map}
    if len(mapped) != len(gap_map):
        raise VerificationError("gap refs must be unique")
    if mapped != set(EXPECTED_GAP_OWNERS):
        raise VerificationError("gap map must match the exact finite gap contract")
    if not observed_gap_refs.issubset(mapped):
        raise VerificationError("component gap is not mapped")
    for item in gap_map:
        _require_exact_keys(item, {"gap_ref", "phase_owner", "terminal_posture"}, "gap map row")
        if item.get("phase_owner") not in {f"phase_{index:02d}" for index in range(1, 10)}:
            raise VerificationError("gap must map to Phase 01-09")
        if not item.get("terminal_posture"):
            raise VerificationError("gap requires terminal posture")
        if item["phase_owner"] != EXPECTED_GAP_OWNERS[item["gap_ref"]]:
            raise VerificationError("gap owner does not match finite gap contract")
        if item["gap_ref"] in expected_gap_owners and item["phase_owner"] != expected_gap_owners[item["gap_ref"]]:
            raise VerificationError("gap owner does not match component owner")

    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list):
        raise VerificationError("scenarios must be a list")
    scenario_ids = tuple(item.get("scenario_id") for item in scenarios)
    if scenario_ids != EXPECTED_SCENARIOS:
        raise VerificationError("scenario ids/order must match the finite twelve-scenario contract")
    for item in scenarios:
        _require_exact_keys(item, {"scenario_id", "phase_refs", "status", "safe_summary"}, "scenario")
        if item.get("status") not in {"mapped_not_run", "passed", "blocked", "external_blocked"}:
            raise VerificationError("invalid scenario status")
        if item.get("phase_refs") != EXPECTED_SCENARIO_PHASES[item["scenario_id"]]:
            raise VerificationError("scenario phase ownership drift")
        if not isinstance(item.get("safe_summary"), str) or not item["safe_summary"].strip():
            raise VerificationError("scenario safe_summary is required")

    if set(data.get("preservation_refs", [])) != REQUIRED_PRESERVATION_REFS:
        raise VerificationError("preservation refs drift")
    if set(data.get("denied_postures", [])) != REQUIRED_DENIALS:
        raise VerificationError("denied postures drift")

    timing_snapshot = data.get("timing_snapshot", {})
    _require_exact_keys(
        timing_snapshot,
        {"runner_profile_ref", "unit", "safe_summary_only", "measurements"},
        "timing snapshot",
    )
    if timing_snapshot.get("runner_profile_ref") != "runner-profile:local-macos":
        raise VerificationError("timing runner profile drift")
    if timing_snapshot.get("unit") != "seconds" or timing_snapshot.get("safe_summary_only") is not True:
        raise VerificationError("timing safety/unit contract drift")
    measurements = timing_snapshot.get("measurements")
    if not isinstance(measurements, list) or len(measurements) != 4:
        raise VerificationError("exactly four timing measurements are required")
    command_refs = tuple(measurement.get("command_ref") for measurement in measurements)
    if command_refs != EXPECTED_TIMING_COMMANDS:
        raise VerificationError("timing command refs/order drift")
    measured_key_sets = {
        EXPECTED_TIMING_COMMANDS[0]: {"command_ref", "status", "samples", "median", "cold_sample", "warm_samples", "test_count", "final_acceptance_test_count", "skipped_count", "shard_count", "worker_count", "diagnostic_samples", "diagnostic_reason_ref", "performance_claimed"},
        EXPECTED_TIMING_COMMANDS[1]: {"command_ref", "status", "samples", "median", "test_count", "test_file_count", "typescript_version"},
        EXPECTED_TIMING_COMMANDS[2]: {"command_ref", "status", "samples", "median", "test_count", "live_network_enabled"},
        EXPECTED_TIMING_COMMANDS[3]: {"command_ref", "status", "samples", "median", "criterion_count", "benchmark_runs_seconds"},
    }
    for measurement in measurements:
        status = measurement.get("status")
        if status not in TIMING_STATUSES:
            raise VerificationError("invalid timing status")
        if status == "pending_measurement" and not allow_pending_timings:
            raise VerificationError("timing measurement remains pending")
        samples = measurement.get("samples")
        if status == "measured":
            _require_exact_keys(
                measurement,
                measured_key_sets[measurement["command_ref"]],
                f"timing {measurement['command_ref']}",
            )
            if not isinstance(samples, list) or not samples or any(
                not isinstance(sample, (int, float)) or sample <= 0 for sample in samples
            ):
                raise VerificationError("measured timing requires positive samples")
            expected_median = Decimal(str(statistics.median(samples))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if Decimal(str(measurement.get("median"))) != expected_median:
                raise VerificationError("timing median drift")
            for count_key, count_value in measurement.items():
                if count_key.endswith("_count") and (
                    not isinstance(count_value, int) or isinstance(count_value, bool) or count_value < 0
                ):
                    raise VerificationError("timing counts must be nonnegative integers")
        elif status == "external_blocked":
            _require_exact_keys(
                measurement,
                {"command_ref", "status", "samples", "median", "blocker_ref"},
                f"external-blocked timing {measurement['command_ref']}",
            )
            if samples != [] or measurement.get("median") is not None or not measurement.get("blocker_ref"):
                raise VerificationError("external_blocked timing requires empty samples and blocker_ref")
        else:
            _require_exact_keys(
                measurement,
                {"command_ref", "status", "samples", "median"},
                f"pending timing {measurement['command_ref']}",
            )
            if samples != [] or measurement.get("median") is not None:
                raise VerificationError("pending timing must have empty samples")

    pytest_timing, frontend_timing, web_timing, foundation_timing = measurements
    if pytest_timing["status"] == "measured" and pytest_timing["samples"] != [pytest_timing["cold_sample"], *pytest_timing["warm_samples"]]:
        raise VerificationError("pytest cold/warm sample partition drift")
    if pytest_timing["status"] == "measured" and (not pytest_timing["warm_samples"] or pytest_timing["shard_count"] != 8 or pytest_timing["worker_count"] != 8):
        raise VerificationError("pytest timing topology drift")
    if pytest_timing["status"] == "measured" and (
        pytest_timing["final_acceptance_test_count"] < pytest_timing["test_count"]
        or pytest_timing["performance_claimed"] is not False
        or not pytest_timing["diagnostic_reason_ref"].startswith("reason-ref:")
        or any(
            not isinstance(sample, (int, float)) or sample <= 0
            for sample in pytest_timing["diagnostic_samples"]
        )
    ):
        raise VerificationError("pytest diagnostic timing posture drift")
    if frontend_timing["status"] == "measured" and frontend_timing["typescript_version"] != "7.0.2":
        raise VerificationError("frontend TypeScript timing baseline drift")
    if web_timing["status"] == "measured" and web_timing["live_network_enabled"] is not False:
        raise VerificationError("WEB-HYBRID timing must remain non-live")
    if foundation_timing["status"] == "measured" and any(not isinstance(sample, (int, float)) or sample <= 0 for sample in foundation_timing["benchmark_runs_seconds"]):
        raise VerificationError("Foundation benchmark runs must be positive")

    redaction = data.get("redaction", {})
    _require_exact_keys(
        redaction,
        {"safe_refs_only", "raw_content_persisted", "local_paths_persisted", "machine_identity_persisted"},
        "redaction",
    )
    expected_redaction = {
        "safe_refs_only": True,
        "raw_content_persisted": False,
        "local_paths_persisted": False,
        "machine_identity_persisted": False,
    }
    if redaction != expected_redaction:
        raise VerificationError("redaction contract drift")


def verify_report(data: dict[str, Any], report_path: Path, benchmark_path: Path) -> None:
    try:
        text = report_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise VerificationError("scoreboard report is missing") from exc
    if REPORT_ABSOLUTE_PATH_PATTERN.search(text):
        raise VerificationError("scoreboard contains an absolute local path")
    required_lines = {
        f"Benchmark data hash: `{_benchmark_hash(benchmark_path)}`",
        f"| UAA | {data['weighted_totals']['uaa']:.1f}/100 |",
        f"| GoatCitadel | {data['weighted_totals']['goatcitadel']:.1f}/100 |",
    }
    for component in data["components"]:
        required_lines.add(
            f"| {component['label']} | {component['weight']} | "
            f"{component['uaa']['score']:.1f} | {component['goatcitadel']['score']:.1f} | "
            f"{component['phase_owner'].replace('_', ' ').title()} |"
        )
    missing = sorted(line for line in required_lines if line not in text)
    if missing:
        raise VerificationError(f"scoreboard drift: missing {missing[0]}")
    for stale in (
        "stop after Phase 01",
        "Merge-Gated Follow-Up Prompts",
        "live web fetching remains blocked",
        "final 30-day plan",
    ):
        if stale.lower() in text.lower():
            raise VerificationError(f"scoreboard contains stale recursive or web truth: {stale}")


def verify(
    benchmark_path: Path = DEFAULT_BENCHMARK,
    report_path: Path = DEFAULT_REPORT,
    *,
    allow_pending_timings: bool = False,
) -> dict[str, Any]:
    data = _load_json(benchmark_path)
    verify_benchmark(data, allow_pending_timings=allow_pending_timings)
    verify_report(data, report_path, benchmark_path)
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--allow-pending-timings", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        data = verify(
            args.benchmark,
            args.report,
            allow_pending_timings=args.allow_pending_timings,
        )
    except VerificationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({
            "schema_version": data["schema_version"],
            "component_count": len(data["components"]),
            "scenario_count": len(data["scenarios"]),
            "uaa_score": data["weighted_totals"]["uaa"],
            "goatcitadel_score": data["weighted_totals"]["goatcitadel"],
        }, sort_keys=True))
    else:
        print("UAA runtime capability benchmark and scoreboard verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
