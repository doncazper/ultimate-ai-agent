#!/usr/bin/env python3
"""Build and compare deterministic repo awareness benchmark snapshots.

This tool is inspection-only unless --write is passed. It reads existing
repo-owned manifests, docs, and reports, then emits safe summary scores. It
does not run tests, execute release lanes, call models, fetch networks, start
background work, or add runtime authority.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = ROOT / "docs" / "benchmarks" / "repo_awareness"
SNAPSHOT_DIR = BENCHMARK_DIR / "snapshots"
LATEST_JSON = BENCHMARK_DIR / "latest.json"
LATEST_MD = BENCHMARK_DIR / "latest.md"
INDEX_MD = BENCHMARK_DIR / "index.md"
SCHEMA_PATH = ROOT / "docs" / "schemas" / "repo_awareness_benchmark.schema.json"

SNAPSHOT_SCHEMA_VERSION = "uaa_repo_awareness_benchmark.v1"
COMPARISON_SCHEMA_VERSION = "uaa_repo_awareness_comparison.v1"
TASK_REF = "UAA-BENCH-001"
SCAN_MODE = "whole_repo_deterministic"
DEFAULT_REASON = "manual_review"

CATEGORY_WEIGHTS = {
    "module_maturity": 20,
    "route_product_surface": 20,
    "verifier_evidence_coverage": 20,
    "safety_boundary_health": 20,
    "performance_state": 10,
    "rc_readiness_blockers": 10,
}

TIERS = (
    ("blocked", 0, 39),
    ("emerging", 40, 59),
    ("stabilizing", 60, 74),
    ("rc_watch", 75, 89),
    ("rc_ready", 90, 100),
)

SCORE_STATUS_WEIGHTS = {
    "status_available_not_completion": 70,
    "preview_available_not_execution": 65,
    "partial_backend_not_product_ready": 55,
    "mock_only_not_product_ready": 30,
    "local_ui_state_only_not_evidence": 35,
    "blocked_missing_backend": 20,
}

RC_STATUS_WEIGHTS = {
    "status_available_not_completion": 75,
    "preview_available_not_execution": 70,
    "partial_backend_not_product_ready": 55,
    "mock_only_not_product_ready": 35,
    "local_ui_state_only_not_evidence": 35,
    "blocked_missing_backend": 20,
}

REPORT_SAFETY = {
    "raw_prompt_included": False,
    "raw_response_included": False,
    "raw_provider_payload_included": False,
    "raw_path_included": False,
    "raw_log_included": False,
    "username_included": False,
    "hostname_included": False,
    "serial_included": False,
    "environment_dump_included": False,
    "credential_material_included": False,
}

FORBIDDEN_RAW_FRAGMENTS = (
    "/users/",
    "\\users\\",
    "raw prompt:",
    "raw response:",
    "raw provider payload:",
    "raw path:",
    "raw log:",
    "username:",
    "hostname:",
    "serial number:",
    "environment dump:",
    "credential:",
    "api_key",
    "secret_key",
    "password=",
    "token=",
)

SAFE_REF_PREFIXES = (
    "baseline:",
    "benchmark:",
    "command:",
    "commit:",
    "report:",
    "schema:",
    "snapshot:",
    "task:",
)

REQUIRED_EVIDENCE_PATHS = (
    "scripts/verify_all.py",
    "scripts/verify_documentation_integrity.py",
    "scripts/verify_openapi_contract.py",
    "scripts/verify_agent_module_maturity_map.py",
    "scripts/verify_release_lanes.py",
    "scripts/verify_release_evidence_packet.py",
    "scripts/benchmark_foundation_gate.py",
    "docs/production/RELEASE_VERIFICATION_LANES.md",
    "docs/production/RELEASE_EVIDENCE_PACKET.md",
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
    "docs/control_center/ROUTE_STATUS_MANIFEST.md",
    "docs/control_center/route_status_manifest.json",
    "tests/test_agent_module_maturity_map.py",
    "tests/test_release_evidence_packet.py",
    "tests/test_foundation_gate_latency_scripts.py",
)

REQUIRED_SAFETY_EVIDENCE_PATHS = (
    "README.md",
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
    "docs/production/RELEASE_EVIDENCE_PACKET_TEMPLATE.json",
    "reports/performance/latest_release_latency_baseline.json",
    "docs/control_center/route_status_manifest.json",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def utc_label(value: datetime | None = None) -> str:
    active = value or utc_now()
    return active.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def compact_utc_label(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", value).lower()


def tier_for_score(score: int) -> str:
    for tier, lower, upper in TIERS:
        if lower <= score <= upper:
            return tier
    raise ValueError(f"score out of tier range: {score}")


def _safe_int(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _load_json(root: Path, rel_path: str) -> dict[str, Any] | None:
    path = root / rel_path
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _repo_rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _safe_commit_ref(root: Path) -> str:
    head_path = root / ".git" / "HEAD"
    if not head_path.exists():
        return "commit:unknown"
    head = head_path.read_text(encoding="utf-8").strip()
    if head.startswith("ref: "):
        ref = head.removeprefix("ref: ").strip()
        ref_path = root / ".git" / ref
        if ref_path.exists():
            candidate = ref_path.read_text(encoding="utf-8").strip()
            if re.fullmatch(r"[a-f0-9]{7,64}", candidate):
                return f"commit:{candidate}"
        packed_refs = root / ".git" / "packed-refs"
        if packed_refs.exists():
            for line in packed_refs.read_text(encoding="utf-8").splitlines():
                if not line or line.startswith("#") or line.startswith("^"):
                    continue
                parts = line.split()
                if len(parts) == 2 and parts[1] == ref and re.fullmatch(r"[a-f0-9]{7,64}", parts[0]):
                    return f"commit:{parts[0]}"
    if re.fullmatch(r"[a-f0-9]{7,64}", head):
        return f"commit:{head}"
    return "commit:unknown"


def _category(
    *,
    category_id: str,
    label: str,
    score: int,
    safe_summary: str,
    evidence_refs: list[str],
    metrics: dict[str, Any],
    blockers: list[str],
) -> dict[str, Any]:
    bounded_score = _safe_int(score)
    return {
        "id": category_id,
        "label": label,
        "score": bounded_score,
        "tier": tier_for_score(bounded_score),
        "safe_summary": safe_summary,
        "evidence_refs": evidence_refs,
        "metrics": metrics,
        "blockers": blockers,
    }


def _score_module_maturity(root: Path) -> dict[str, Any]:
    evidence_ref = "docs/registry/agent_module_maturity_map.json"
    payload = _load_json(root, evidence_ref)
    if payload is None:
        return _category(
            category_id="module_maturity",
            label="Module maturity",
            score=0,
            safe_summary="Module maturity map is missing or invalid.",
            evidence_refs=[evidence_ref],
            metrics={"module_count": 0},
            blockers=["module_maturity_map_missing_or_invalid"],
        )
    modules = payload.get("modules")
    if not isinstance(modules, list) or not modules:
        return _category(
            category_id="module_maturity",
            label="Module maturity",
            score=0,
            safe_summary="Module maturity map has no module entries.",
            evidence_refs=[evidence_ref],
            metrics={"module_count": 0},
            blockers=["module_maturity_entries_missing"],
        )
    scores = [
        module.get("maturity_score")
        for module in modules
        if isinstance(module, dict) and isinstance(module.get("maturity_score"), int)
    ]
    score = _safe_int((sum(scores) / (len(scores) * 6)) * 100) if scores else 0
    low_modules = [
        str(module.get("id"))
        for module in modules
        if isinstance(module, dict) and isinstance(module.get("maturity_score"), int) and module["maturity_score"] < 3
    ]
    distribution: dict[str, int] = {}
    for module_score in scores:
        distribution[str(module_score)] = distribution.get(str(module_score), 0) + 1
    return _category(
        category_id="module_maturity",
        label="Module maturity",
        score=score,
        safe_summary="Average requested-module maturity derived from the active module maturity map.",
        evidence_refs=[evidence_ref, "scripts/verify_agent_module_maturity_map.py"],
        metrics={
            "module_count": len(modules),
            "average_maturity_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "max_maturity_score": max(scores) if scores else 0,
            "score_distribution": distribution,
            "modules_below_validated_contract": len(low_modules),
        },
        blockers=[f"module_below_validated_contract:{module_id}" for module_id in low_modules],
    )


def _score_route_product_surface(root: Path) -> dict[str, Any]:
    evidence_ref = "docs/control_center/route_status_manifest.json"
    payload = _load_json(root, evidence_ref)
    if payload is None:
        return _category(
            category_id="route_product_surface",
            label="Route and product surface",
            score=0,
            safe_summary="Route status manifest is missing or invalid.",
            evidence_refs=[evidence_ref],
            metrics={"entry_count": 0},
            blockers=["route_status_manifest_missing_or_invalid"],
        )
    entries = []
    for section in ("surfaces", "visible_actions"):
        values = payload.get(section)
        if isinstance(values, list):
            entries.extend(item for item in values if isinstance(item, dict))
    scored = [SCORE_STATUS_WEIGHTS.get(str(item.get("release_status")), 0) for item in entries]
    score = _safe_int(sum(scored) / len(scored)) if scored else 0
    status_counts: dict[str, int] = {}
    blockers: list[str] = []
    for item in entries:
        status = str(item.get("release_status", "unknown"))
        status_counts[status] = status_counts.get(status, 0) + 1
        if status in {"blocked_missing_backend", "mock_only_not_product_ready"}:
            name = str(item.get("surface") or item.get("action_id") or "unknown")
            blockers.append(f"{status}:{name}")
    return _category(
        category_id="route_product_surface",
        label="Route and product surface",
        score=score,
        safe_summary="Control Center surfaces and visible actions scored from explicit route release statuses.",
        evidence_refs=[evidence_ref, "docs/control_center/ROUTE_STATUS_MANIFEST.md"],
        metrics={
            "surface_count": len(payload.get("surfaces", [])) if isinstance(payload.get("surfaces"), list) else 0,
            "visible_action_count": len(payload.get("visible_actions", []))
            if isinstance(payload.get("visible_actions"), list)
            else 0,
            "status_counts": status_counts,
            "openapi_path_count": payload.get("openapi_path_count"),
        },
        blockers=blockers,
    )


def _score_verifier_evidence_coverage(root: Path) -> dict[str, Any]:
    present = [rel_path for rel_path in REQUIRED_EVIDENCE_PATHS if (root / rel_path).exists()]
    missing = [rel_path for rel_path in REQUIRED_EVIDENCE_PATHS if rel_path not in present]
    score = _safe_int((len(present) / len(REQUIRED_EVIDENCE_PATHS)) * 100)
    return _category(
        category_id="verifier_evidence_coverage",
        label="Verifier and evidence coverage",
        score=score,
        safe_summary="Required verifier, release-evidence, product-truth, and maturity-map paths checked for presence.",
        evidence_refs=list(REQUIRED_EVIDENCE_PATHS),
        metrics={
            "required_evidence_paths": len(REQUIRED_EVIDENCE_PATHS),
            "present_evidence_paths": len(present),
            "missing_evidence_paths": len(missing),
        },
        blockers=[f"missing_evidence_path:{rel_path}" for rel_path in missing],
    )


def _all_false(value: Any) -> bool:
    return isinstance(value, dict) and all(flag is False for flag in value.values())


def _score_safety_boundary_health(root: Path) -> dict[str, Any]:
    checks: list[tuple[str, bool]] = []
    route_manifest = _load_json(root, "docs/control_center/route_status_manifest.json")
    release_template = _load_json(root, "docs/production/RELEASE_EVIDENCE_PACKET_TEMPLATE.json")
    perf_report = _load_json(root, "reports/performance/latest_release_latency_baseline.json")
    product_truth = root / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"

    checks.append(
        (
            "route_manifest_default_posture_contract_first",
            isinstance(route_manifest, dict)
            and str(route_manifest.get("default_posture", "")).startswith("contract_first"),
        )
    )
    checks.append(
        (
            "release_packet_safety_flags_false",
            isinstance(release_template, dict) and _all_false(release_template.get("packet_safety")),
        )
    )
    checks.append(
        (
            "performance_report_safety_flags_false",
            isinstance(perf_report, dict) and _all_false(perf_report.get("report_safety")),
        )
    )
    authority = perf_report.get("authority_invariants") if isinstance(perf_report, dict) else {}
    checks.extend(
        [
            ("policy_engine_not_bypassed", isinstance(authority, dict) and authority.get("policy_engine_bypassed_for_speed") is False),
            (
                "local_approval_authority_not_bypassed",
                isinstance(authority, dict) and authority.get("local_approval_authority_bypassed_for_speed") is False,
            ),
            ("openapi_checks_preserved", isinstance(authority, dict) and authority.get("openapi_checks_preserved") is True),
            (
                "foundation_gate_checks_preserved",
                isinstance(authority, dict) and authority.get("foundation_gate_checks_preserved") is True,
            ),
            (
                "product_truth_non_goals_present",
                product_truth.exists() and "Do not claim production readiness" in product_truth.read_text(encoding="utf-8"),
            ),
        ]
    )
    passed = [name for name, ok in checks if ok]
    failed = [name for name, ok in checks if not ok]
    score = _safe_int((len(passed) / len(checks)) * 100)
    return _category(
        category_id="safety_boundary_health",
        label="Safety boundary health",
        score=score,
        safe_summary="Safety score checks disabled-by-default posture, false raw-data flags, and preserved authority invariants.",
        evidence_refs=list(REQUIRED_SAFETY_EVIDENCE_PATHS),
        metrics={
            "safety_checks": len(checks),
            "passed_safety_checks": len(passed),
            "failed_safety_checks": len(failed),
            "passed_check_ids": passed,
        },
        blockers=[f"safety_check_failed:{name}" for name in failed],
    )


def _score_performance_state(root: Path) -> dict[str, Any]:
    evidence_ref = "reports/performance/latest_release_latency_baseline.json"
    report = _load_json(root, evidence_ref)
    if report is None:
        return _category(
            category_id="performance_state",
            label="Performance state",
            score=0,
            safe_summary="Latest release latency report is missing or invalid.",
            evidence_refs=[evidence_ref],
            metrics={"required_path_count": 0},
            blockers=["performance_report_missing_or_invalid"],
        )
    path_results = report.get("path_results")
    required = [
        row
        for row in path_results
        if isinstance(row, dict) and row.get("required") is True
    ] if isinstance(path_results, list) else []
    passed = [
        row
        for row in required
        if row.get("status") == "passed" and row.get("budget_passed") is True
    ]
    score = _safe_int((len(passed) / len(required)) * 100) if required else 0
    if report.get("overall_status") != "passed":
        score = min(score, 75)
    blockers = [
        f"performance_path_not_passing:{row.get('path_id', 'unknown')}"
        for row in required
        if row not in passed
    ]
    return _category(
        category_id="performance_state",
        label="Performance state",
        score=score,
        safe_summary="Required release-critical local latency paths scored from the latest performance report.",
        evidence_refs=[
            evidence_ref,
            "reports/performance/latest_performance_regression_report.json",
            "scripts/benchmark_foundation_gate.py",
        ],
        metrics={
            "overall_status": report.get("overall_status"),
            "required_path_count": len(required),
            "required_paths_passed": len(passed),
            "path_repeat": report.get("path_repeat"),
            "generated_at_utc": report.get("generated_at_utc"),
        },
        blockers=blockers,
    )


def _score_rc_readiness_blockers(root: Path) -> dict[str, Any]:
    route_manifest = _load_json(root, "docs/control_center/route_status_manifest.json")
    docs_present = [
        rel_path
        for rel_path in (
            "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
            "docs/production/RELEASE_EVIDENCE_PACKET.md",
            "docs/production/RELEASE_VERIFICATION_LANES.md",
        )
        if (root / rel_path).exists()
    ]
    surfaces = []
    if isinstance(route_manifest, dict) and isinstance(route_manifest.get("surfaces"), list):
        surfaces = [item for item in route_manifest["surfaces"] if isinstance(item, dict)]
    surface_scores = [RC_STATUS_WEIGHTS.get(str(item.get("release_status")), 0) for item in surfaces]
    surface_score = _safe_int(sum(surface_scores) / len(surface_scores)) if surface_scores else 0
    docs_score = _safe_int((len(docs_present) / 3) * 100)
    score = _safe_int(surface_score * 0.7 + docs_score * 0.3)
    blockers = [
        f"rc_surface_not_ready:{item.get('surface', 'unknown')}:{item.get('release_status', 'unknown')}"
        for item in surfaces
        if item.get("release_status") != "status_available_not_completion"
    ]
    if len(docs_present) < 3:
        blockers.extend("missing_rc_doc:" + rel_path for rel_path in {
            "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
            "docs/production/RELEASE_EVIDENCE_PACKET.md",
            "docs/production/RELEASE_VERIFICATION_LANES.md",
        } - set(docs_present))
    return _category(
        category_id="rc_readiness_blockers",
        label="RC readiness blockers",
        score=score,
        safe_summary="RC readiness uses product-truth docs plus Control Center surface blockers, without claiming release readiness.",
        evidence_refs=[
            "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
            "docs/production/RELEASE_EVIDENCE_PACKET.md",
            "docs/production/RELEASE_VERIFICATION_LANES.md",
            "docs/control_center/route_status_manifest.json",
        ],
        metrics={
            "surface_count": len(surfaces),
            "surface_score": surface_score,
            "rc_docs_present": len(docs_present),
            "rc_doc_score": docs_score,
            "rc_surface_blockers": len(blockers),
        },
        blockers=blockers,
    )


def _overall_score(categories: list[dict[str, Any]]) -> int:
    by_id = {category["id"]: category for category in categories}
    weighted = 0
    total_weight = 0
    for category_id, weight in CATEGORY_WEIGHTS.items():
        category = by_id.get(category_id)
        if category is None:
            continue
        weighted += int(category["score"]) * weight
        total_weight += weight
    return _safe_int(weighted / total_weight) if total_weight else 0


def build_snapshot(
    *,
    root: Path = ROOT,
    reason: str = DEFAULT_REASON,
    generated_at: datetime | None = None,
    commit_ref: str | None = None,
) -> dict[str, Any]:
    generated_label = utc_label(generated_at)
    safe_reason = _slug(reason)
    categories = [
        _score_module_maturity(root),
        _score_route_product_surface(root),
        _score_verifier_evidence_coverage(root),
        _score_safety_boundary_health(root),
        _score_performance_state(root),
        _score_rc_readiness_blockers(root),
    ]
    overall = _overall_score(categories)
    baseline = _read_baseline_ref(root)
    benchmark_id = f"repo-awareness-benchmark:{compact_utc_label(generated_label)}:{safe_reason}"
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "task_ref": TASK_REF,
        "benchmark_id": benchmark_id,
        "generated_at_utc": generated_label,
        "reason": safe_reason,
        "scan_mode": SCAN_MODE,
        "baseline_ref": baseline,
        "commit_ref": commit_ref or _safe_commit_ref(root),
        "score_summary": {
            "overall_score": overall,
            "overall_tier": tier_for_score(overall),
            "category_weights": CATEGORY_WEIGHTS,
            "safe_summary": "Deterministic repo awareness score based only on tracked repo evidence and safe report refs.",
        },
        "categories": categories,
        "weekly_review_model": {
            "mode": "reminder_plus_manual_command",
            "command": ".venv/bin/python scripts/benchmark_repo_awareness.py snapshot --reason weekly_review --write",
            "unattended_repo_writes": False,
            "auto_commit": False,
        },
        "non_goals": [
            "no backend routes",
            "no Control Center UI surface",
            "no model calls",
            "no network fetches",
            "no background workers",
            "no new dependencies",
            "no production authority",
        ],
        "report_safety": REPORT_SAFETY,
    }


def _read_baseline_ref(root: Path) -> str:
    version_path = root / "VERSION"
    if version_path.exists():
        version = version_path.read_text(encoding="utf-8").strip()
        if version:
            return f"baseline:v{version}" if not version.startswith("v") else f"baseline:{version}"
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8"), re.MULTILINE)
        if match:
            return f"baseline:v{match.group(1)}"
    return "baseline:unknown"


def _slug(value: str) -> str:
    lowered = value.strip().lower().replace("_", "-")
    slug = re.sub(r"[^a-z0-9.-]+", "-", lowered).strip("-")
    return slug or DEFAULT_REASON


def _snapshot_filename(snapshot: dict[str, Any]) -> str:
    generated = compact_utc_label(str(snapshot["generated_at_utc"]))
    reason = _slug(str(snapshot.get("reason", DEFAULT_REASON)))
    return f"{generated}_{reason}.json"


def write_snapshot(snapshot: dict[str, Any], *, root: Path = ROOT) -> dict[str, str]:
    benchmark_dir = root / "docs" / "benchmarks" / "repo_awareness"
    snapshot_dir = benchmark_dir / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_dir / _snapshot_filename(snapshot)
    _write_json(snapshot_path, snapshot)
    _write_json(benchmark_dir / "latest.json", snapshot)
    (benchmark_dir / "latest.md").write_text(markdown_for_snapshot(snapshot), encoding="utf-8")
    (benchmark_dir / "index.md").write_text(index_markdown(root=root), encoding="utf-8")
    return {
        "snapshot_json": _repo_rel(root, snapshot_path),
        "latest_json": "docs/benchmarks/repo_awareness/latest.json",
        "latest_md": "docs/benchmarks/repo_awareness/latest.md",
        "index_md": "docs/benchmarks/repo_awareness/index.md",
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def markdown_for_snapshot(snapshot: dict[str, Any]) -> str:
    lines = [
        "# Repo Awareness Benchmark",
        "",
        "Status: tracked deterministic snapshot",
        f"Generated: {snapshot['generated_at_utc']}",
        f"Reason: `{snapshot['reason']}`",
        f"Baseline: `{snapshot['baseline_ref']}`",
        f"Commit: `{snapshot['commit_ref']}`",
        "",
        "This benchmark is a repo-owned self-grade. It records safe summaries, scores, blockers, and evidence refs only.",
        "",
        "## Score",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Overall score | {snapshot['score_summary']['overall_score']} |",
        f"| Overall tier | `{snapshot['score_summary']['overall_tier']}` |",
        "",
        "## Categories",
        "",
        "| Category | Score | Tier | Blockers |",
        "|---|---:|---|---:|",
    ]
    for category in snapshot["categories"]:
        lines.append(
            f"| {category['label']} | {category['score']} | `{category['tier']}` | {len(category['blockers'])} |"
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Raw prompts included: false",
            "- Raw responses included: false",
            "- Raw provider payloads included: false",
            "- Raw paths or logs included: false",
            "- Weekly automatic model: reminder plus manual command, no auto-commit",
            "",
            "## Rollback",
            "",
            "Delete this snapshot file plus `latest.json`, `latest.md`, and `index.md` updates for the benchmark run being reverted.",
            "",
        ]
    )
    return "\n".join(lines)


def index_markdown(*, root: Path = ROOT) -> str:
    benchmark_dir = root / "docs" / "benchmarks" / "repo_awareness"
    snapshot_dir = benchmark_dir / "snapshots"
    snapshots = sorted(_load_snapshot_files(snapshot_dir), key=lambda item: item["generated_at_utc"], reverse=True)
    lines = [
        "# Repo Awareness Benchmark Index",
        "",
        "Status: active deterministic benchmark ledger",
        "",
        "Use:",
        "",
        "```bash",
        ".venv/bin/python scripts/benchmark_repo_awareness.py snapshot --reason manual_review --write",
        ".venv/bin/python scripts/benchmark_repo_awareness.py compare --since 7d",
        "```",
        "",
        "| Generated | Reason | Score | Tier | Snapshot |",
        "|---|---|---:|---|---|",
    ]
    if not snapshots:
        lines.append("| none | none | 0 | `blocked` | none |")
    for item in snapshots:
        rel_path = _repo_rel(root, Path(item["_path"]))
        lines.append(
            f"| {item['generated_at_utc']} | `{item.get('reason', 'manual_review')}` | "
            f"{item['score_summary']['overall_score']} | `{item['score_summary']['overall_tier']}` | `{rel_path}` |"
        )
    lines.append("")
    return "\n".join(lines)


def _load_snapshot_files(snapshot_dir: Path) -> list[dict[str, Any]]:
    if not snapshot_dir.exists():
        return []
    snapshots: list[dict[str, Any]] = []
    for path in snapshot_dir.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("schema_version") == SNAPSHOT_SCHEMA_VERSION:
            payload["_path"] = str(path)
            snapshots.append(payload)
    return snapshots


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _duration(value: str) -> timedelta:
    match = re.fullmatch(r"(\d+)([hdw])", value.strip().lower())
    if not match:
        raise argparse.ArgumentTypeError("--since must look like 24h, 7d, or 2w")
    amount = int(match.group(1))
    unit = match.group(2)
    if unit == "h":
        return timedelta(hours=amount)
    if unit == "d":
        return timedelta(days=amount)
    return timedelta(weeks=amount)


def _load_snapshot_path(root: Path, value: str) -> dict[str, Any]:
    path = Path(value)
    if not path.is_absolute():
        candidate = root / value
        if not candidate.exists():
            candidate = root / "docs" / "benchmarks" / "repo_awareness" / value
        path = candidate
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"snapshot must be an object: {value}")
    return payload


def find_prior_snapshot(*, root: Path = ROOT, since: str, now: datetime | None = None) -> dict[str, Any] | None:
    target = (now or utc_now()) - _duration(since)
    snapshots = _load_snapshot_files(root / "docs" / "benchmarks" / "repo_awareness" / "snapshots")
    candidates = [
        snapshot
        for snapshot in snapshots
        if _parse_time(str(snapshot["generated_at_utc"])) <= target
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item["generated_at_utc"], reverse=True)[0]


def latest_snapshot(*, root: Path = ROOT) -> dict[str, Any] | None:
    latest = root / "docs" / "benchmarks" / "repo_awareness" / "latest.json"
    if latest.exists():
        payload = json.loads(latest.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    snapshots = _load_snapshot_files(root / "docs" / "benchmarks" / "repo_awareness" / "snapshots")
    if not snapshots:
        return None
    return sorted(snapshots, key=lambda item: item["generated_at_utc"], reverse=True)[0]


def compare_snapshots(
    from_snapshot: dict[str, Any] | None,
    to_snapshot: dict[str, Any],
    *,
    since: str | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    comparison_id = f"repo-awareness-comparison:{compact_utc_label(utc_label(generated_at))}"
    if from_snapshot is None:
        return {
            "schema_version": COMPARISON_SCHEMA_VERSION,
            "comparison_id": comparison_id,
            "generated_at_utc": utc_label(generated_at),
            "status": "no_prior_snapshot",
            "since": since,
            "from_benchmark_id": None,
            "to_benchmark_id": to_snapshot.get("benchmark_id"),
            "overall_delta": None,
            "category_deltas": [],
            "safe_summary": "No prior benchmark snapshot exists for the requested comparison window.",
            "comparison_safety": REPORT_SAFETY,
        }
    from_score = int(from_snapshot["score_summary"]["overall_score"])
    to_score = int(to_snapshot["score_summary"]["overall_score"])
    from_categories = {category["id"]: category for category in from_snapshot.get("categories", [])}
    category_deltas = []
    for to_category in to_snapshot.get("categories", []):
        prior = from_categories.get(to_category["id"])
        if prior is None:
            delta = None
            direction = "new"
            from_value = None
        else:
            from_value = int(prior["score"])
            delta = int(to_category["score"]) - from_value
            direction = "improved" if delta > 0 else "regressed" if delta < 0 else "unchanged"
        category_deltas.append(
            {
                "category_id": to_category["id"],
                "from_score": from_value,
                "to_score": int(to_category["score"]),
                "delta": delta,
                "direction": direction,
                "from_tier": prior.get("tier") if prior else None,
                "to_tier": to_category.get("tier"),
            }
        )
    return {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "comparison_id": comparison_id,
        "generated_at_utc": utc_label(generated_at),
        "status": "compared",
        "since": since,
        "from_benchmark_id": from_snapshot.get("benchmark_id"),
        "to_benchmark_id": to_snapshot.get("benchmark_id"),
        "from_generated_at_utc": from_snapshot.get("generated_at_utc"),
        "to_generated_at_utc": to_snapshot.get("generated_at_utc"),
        "overall_delta": to_score - from_score,
        "category_deltas": category_deltas,
        "improved_categories": [item["category_id"] for item in category_deltas if item["direction"] == "improved"],
        "regressed_categories": [item["category_id"] for item in category_deltas if item["direction"] == "regressed"],
        "unchanged_categories": [item["category_id"] for item in category_deltas if item["direction"] == "unchanged"],
        "safe_summary": "Score deltas compare deterministic repo awareness snapshots.",
        "comparison_safety": REPORT_SAFETY,
    }


def markdown_for_comparison(comparison: dict[str, Any]) -> str:
    lines = [
        "# Repo Awareness Benchmark Comparison",
        "",
        f"Status: `{comparison['status']}`",
        f"Generated: {comparison['generated_at_utc']}",
        "",
    ]
    if comparison["status"] == "no_prior_snapshot":
        lines.append(comparison["safe_summary"])
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            f"From: `{comparison['from_benchmark_id']}`",
            f"To: `{comparison['to_benchmark_id']}`",
            f"Overall delta: `{comparison['overall_delta']}`",
            "",
            "| Category | From | To | Delta | Direction |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for item in comparison["category_deltas"]:
        lines.append(
            f"| {item['category_id']} | {item['from_score']} | {item['to_score']} | {item['delta']} | `{item['direction']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def validate_benchmark_snapshot(payload: dict[str, Any], *, root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    if payload.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        failures.append("schema_version must be uaa_repo_awareness_benchmark.v1")
    if payload.get("task_ref") != TASK_REF:
        failures.append("task_ref must be UAA-BENCH-001")
    if payload.get("scan_mode") != SCAN_MODE:
        failures.append("scan_mode must be whole_repo_deterministic")
    for field in ("benchmark_id", "generated_at_utc", "reason", "baseline_ref", "commit_ref"):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            failures.append(f"{field} must be a non-empty string")
    score_summary = payload.get("score_summary")
    if not isinstance(score_summary, dict):
        failures.append("score_summary must be an object")
        score_summary = {}
    overall_score = score_summary.get("overall_score")
    overall_tier = score_summary.get("overall_tier")
    if not isinstance(overall_score, int) or not 0 <= overall_score <= 100:
        failures.append("overall_score must be an integer from 0 to 100")
    elif overall_tier != tier_for_score(overall_score):
        failures.append("overall_tier does not match overall_score")
    categories = payload.get("categories")
    if not isinstance(categories, list) or not categories:
        failures.append("categories must be a non-empty list")
        categories = []
    category_ids = [category.get("id") for category in categories if isinstance(category, dict)]
    if set(category_ids) != set(CATEGORY_WEIGHTS):
        failures.append("categories must cover the required category ids exactly")
    for category in categories:
        if not isinstance(category, dict):
            failures.append("category entries must be objects")
            continue
        category_id = str(category.get("id"))
        score = category.get("score")
        if not isinstance(score, int) or not 0 <= score <= 100:
            failures.append(f"{category_id}: score must be an integer from 0 to 100")
        elif category.get("tier") != tier_for_score(score):
            failures.append(f"{category_id}: tier does not match score")
        if not isinstance(category.get("safe_summary"), str) or not category["safe_summary"].strip():
            failures.append(f"{category_id}: safe_summary must be a non-empty string")
        evidence_refs = category.get("evidence_refs")
        if not isinstance(evidence_refs, list) or not evidence_refs:
            failures.append(f"{category_id}: evidence_refs must be a non-empty list")
        else:
            for evidence_ref in evidence_refs:
                if not isinstance(evidence_ref, str) or not evidence_ref.strip():
                    failures.append(f"{category_id}: evidence_ref entries must be non-empty strings")
                    continue
                if not _is_safe_existing_evidence_ref(root, evidence_ref):
                    failures.append(f"{category_id}: evidence ref is not a safe known ref: {evidence_ref}")
        if not isinstance(category.get("metrics"), dict):
            failures.append(f"{category_id}: metrics must be an object")
        if not isinstance(category.get("blockers"), list):
            failures.append(f"{category_id}: blockers must be a list")
    if isinstance(overall_score, int) and categories:
        expected = _overall_score(categories)
        if overall_score != expected:
            failures.append(f"overall_score {overall_score} does not match weighted category score {expected}")
    if payload.get("report_safety") != REPORT_SAFETY:
        failures.append("report_safety flags must all be false and complete")
    text = json.dumps(payload, sort_keys=True).lower()
    for fragment in FORBIDDEN_RAW_FRAGMENTS:
        if fragment in text:
            failures.append(f"snapshot contains forbidden raw/private fragment: {fragment}")
    return failures


def _is_safe_existing_evidence_ref(root: Path, evidence_ref: str) -> bool:
    if evidence_ref.startswith(SAFE_REF_PREFIXES):
        return True
    path = Path(evidence_ref)
    if path.is_absolute() or ".." in path.parts:
        return False
    return (root / path).exists()


def validate_repo_awareness_benchmark(*, root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    required_files = [
        "scripts/benchmark_repo_awareness.py",
        "scripts/verify_repo_awareness_benchmark.py",
        "docs/schemas/repo_awareness_benchmark.schema.json",
        "docs/benchmarks/repo_awareness/README.md",
        "docs/benchmarks/repo_awareness/index.md",
        "docs/benchmarks/repo_awareness/latest.json",
        "docs/benchmarks/repo_awareness/latest.md",
        "tests/test_repo_awareness_benchmark.py",
    ]
    for rel_path in required_files:
        if not (root / rel_path).exists():
            failures.append(f"missing required benchmark file: {rel_path}")
    schema = _load_json(root, "docs/schemas/repo_awareness_benchmark.schema.json")
    if schema is None:
        failures.append("repo awareness benchmark schema is missing or invalid")
    else:
        if schema.get("title") != "uaa_repo_awareness_benchmark":
            failures.append("repo awareness benchmark schema title drifted")
        schema_version = schema.get("properties", {}).get("schema_version", {}).get("const")
        if schema_version != SNAPSHOT_SCHEMA_VERSION:
            failures.append("repo awareness benchmark schema_version const drifted")
    latest = _load_json(root, "docs/benchmarks/repo_awareness/latest.json")
    if latest is not None:
        failures.extend(validate_benchmark_snapshot(latest, root=root))
        snapshot_path = root / "docs" / "benchmarks" / "repo_awareness" / "snapshots" / _snapshot_filename(latest)
        if not snapshot_path.exists():
            failures.append(f"latest snapshot file is missing from snapshots directory: {_repo_rel(root, snapshot_path)}")
    snapshots = _load_snapshot_files(root / "docs" / "benchmarks" / "repo_awareness" / "snapshots")
    if not snapshots:
        failures.append("at least one repo awareness benchmark snapshot is required")
    for snapshot in snapshots:
        snapshot.pop("_path", None)
        failures.extend(validate_benchmark_snapshot(snapshot, root=root))
    return failures


def _print_payload(payload: dict[str, Any], *, as_json: bool, markdown: str) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(markdown)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and compare deterministic repo awareness benchmarks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot_parser = subparsers.add_parser("snapshot", help="Build a repo awareness benchmark snapshot.")
    snapshot_parser.add_argument("--reason", default=DEFAULT_REASON, help="Safe reason label for this snapshot.")
    snapshot_parser.add_argument("--write", action="store_true", help="Write tracked snapshot, latest JSON/Markdown, and index.")
    snapshot_parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")

    compare_parser = subparsers.add_parser("compare", help="Compare benchmark snapshots.")
    compare_group = compare_parser.add_mutually_exclusive_group(required=True)
    compare_group.add_argument("--since", help="Compare latest snapshot with the newest snapshot at or before this window, e.g. 24h or 7d.")
    compare_group.add_argument("--from", dest="from_path", help="Snapshot path or benchmark-local snapshot filename to compare from.")
    compare_parser.add_argument("--to", dest="to_path", help="Snapshot path or benchmark-local snapshot filename to compare to. Defaults to latest.")
    compare_parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")

    args = parser.parse_args(argv)
    if args.command == "snapshot":
        snapshot = build_snapshot(reason=args.reason)
        failures = validate_benchmark_snapshot(snapshot)
        if failures:
            for failure in failures:
                print(f"FAIL: {failure}", file=sys.stderr)
            return 1
        if args.write:
            refs = write_snapshot(snapshot)
            snapshot = {**snapshot, "write_refs": refs}
        _print_payload(snapshot, as_json=args.json, markdown=markdown_for_snapshot(snapshot))
        return 0

    if args.command == "compare":
        to_snapshot = _load_snapshot_path(ROOT, args.to_path) if args.to_path else latest_snapshot()
        if to_snapshot is None:
            print("FAIL: no latest benchmark snapshot found", file=sys.stderr)
            return 1
        if args.since:
            from_snapshot = find_prior_snapshot(since=args.since)
            comparison = compare_snapshots(from_snapshot, to_snapshot, since=args.since)
        else:
            from_snapshot = _load_snapshot_path(ROOT, args.from_path)
            comparison = compare_snapshots(from_snapshot, to_snapshot)
        _print_payload(comparison, as_json=args.json, markdown=markdown_for_comparison(comparison))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
