#!/usr/bin/env python3
"""Verify UAA-P1-088 Agent Module Maturity Review V2.

This verifier is inspection-only. It validates repo-owned review artifacts and
does not run tests, call models, fetch networks, execute shell commands, open a
browser, write connectors, mutate memory, inject context, or execute actions.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_agent_module_maturity_map import REQUIRED_MODULE_IDS, verify as verify_v1_map  # noqa: E402

REVIEW_JSON = Path("docs/registry/agent_module_maturity_review_v2.json")
REVIEW_MD = Path("docs/registry/AGENT_MODULE_MATURITY_REVIEW_V2.md")
BENCHMARK_SCRIPT = Path("scripts/benchmark_repo_awareness.py")

REQUIRED_SCHEMA_VERSION = "uaa_agent_module_maturity_review.v2"
REQUIRED_TASK_REF = "UAA-P1-088"
REQUIRED_DIMENSIONS = (
    "product_usefulness",
    "safety_boundary_clarity",
    "test_depth",
    "ui_visibility",
    "cli_parity",
    "evidence_quality",
    "operator_ergonomics",
    "implementation_maturity",
)
REQUIRED_AUTHORITY_FLAGS = (
    "runtime_model_calls_added",
    "provider_sdk_calls_added",
    "web_fetching_added",
    "browser_automation_added",
    "shell_or_subprocess_execution_added",
    "connector_writes_added",
    "memory_writes_added",
    "context_injection_added",
    "action_execution_added",
    "workflow_execution_added",
    "autonomous_routing_authority_added",
    "production_or_public_beta_claim_added",
)
REQUIRED_MODULE_FIELDS = {
    "module_id",
    "module_name",
    "current_maturity",
    "current_maturity_score",
    "current_score",
    "prior_score",
    "prior_score_ref",
    "evidence_refs",
    "implemented_capabilities",
    "missing_capabilities",
    "gaps",
    "blocked_authorities",
    "test_coverage_refs",
    "doc_refs",
    "operator_surface_refs",
    "risk_notes",
    "next_checkpoint",
    "ranked_next_checkpoint",
    "recommended_next_task_ref",
    "dimension_scores",
    "composite_score",
}
MODULE_REF_FIELDS = ("evidence_refs", "test_coverage_refs", "doc_refs", "operator_surface_refs")
MODULE_TEXT_LIST_FIELDS = (
    "implemented_capabilities",
    "missing_capabilities",
    "gaps",
    "blocked_authorities",
    "risk_notes",
)
REQUIRED_QUEUE = (
    "UAA-P1-089",
    "UAA-P1-090",
    "FCC-LOOP-002",
    "FCC-MEM-022",
)
WEAK_MODULES = {"decision_router", "task_decomposition_module"}
TASK_OWNED_PYTHON_REFS = (
    Path("scripts/verify_uaa_p1_088_agent_module_maturity_review_v2.py"),
    Path("tests/test_uaa_p1_088_agent_module_maturity_review_v2.py"),
    BENCHMARK_SCRIPT,
)
FORBIDDEN_IMPORT_ROOTS = {
    "anthropic",
    "boto3",
    "httpx",
    "openai",
    "playwright",
    "requests",
    "selenium",
    "socket",
    "subprocess",
    "urllib",
    "webbrowser",
}
FORBIDDEN_CALL_ROOTS = {
    "eval",
    "exec",
    "openai",
    "os.system",
    "requests",
    "subprocess",
}
FORBIDDEN_POSITIVE_CLAIMS = (
    "production ready",
    "production-ready",
    "public beta enabled",
    "public beta is complete",
    "public release enabled",
    "runtime model calls enabled",
    "context injection enabled",
    "autonomous routing authority enabled",
    "workflow execution enabled",
)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: top-level payload must be an object")
    return payload


def _validate_relative_existing_path(root: Path, rel_path: str, field_name: str) -> str | None:
    path = Path(rel_path)
    if path.is_absolute():
        return f"{field_name} must use repo-relative paths, got absolute path: {rel_path}"
    if ".." in path.parts:
        return f"{field_name} must not traverse outside the repo: {rel_path}"
    if not (root / path).exists():
        return f"{field_name} references missing path: {rel_path}"
    return None


def _expect_non_empty_string(value: Any, field_name: str, failures: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        failures.append(f"{field_name} must be a non-empty string")


def _expect_non_empty_string_list(value: Any, field_name: str, failures: list[str]) -> None:
    if not isinstance(value, list) or not value:
        failures.append(f"{field_name} must be a non-empty list")
        return
    for item in value:
        if not isinstance(item, str) or not item.strip():
            failures.append(f"{field_name} entries must be non-empty strings")


def _expected_composite(scores: dict[str, Any]) -> int | None:
    values: list[int] = []
    for dimension in REQUIRED_DIMENSIONS:
        score = scores.get(dimension)
        if not isinstance(score, int) or not 0 <= score <= 5:
            return None
        values.append(score)
    return sum(values) * 100 // (len(REQUIRED_DIMENSIONS) * 5)


def _validate_post_mem_context(payload: dict[str, Any], root: Path, failures: list[str]) -> None:
    context = payload.get("post_fcc_mem_015_021_context")
    if not isinstance(context, dict):
        failures.append("post_fcc_mem_015_021_context must be an object")
        return
    expected_range = [f"FCC-MEM-{index:03d}" for index in range(15, 22)]
    if context.get("requested_refresh_range") != expected_range:
        failures.append("post_fcc_mem_015_021_context.requested_refresh_range must cover FCC-MEM-015..021")
    _expect_non_empty_string(context.get("tracked_artifact_status"), "post_fcc_mem_015_021_context.tracked_artifact_status", failures)
    tracked_refs = context.get("current_tracked_memory_refs")
    _expect_non_empty_string_list(tracked_refs, "post_fcc_mem_015_021_context.current_tracked_memory_refs", failures)
    if isinstance(tracked_refs, list):
        for ref in tracked_refs:
            if isinstance(ref, str):
                failure = _validate_relative_existing_path(root, ref, "post_fcc_mem_015_021_context.current_tracked_memory_refs")
                if failure:
                    failures.append(failure)
    absent_refs = context.get("absent_tracked_refs")
    _expect_non_empty_string_list(absent_refs, "post_fcc_mem_015_021_context.absent_tracked_refs", failures)
    if isinstance(absent_refs, list):
        for ref in absent_refs:
            if not isinstance(ref, str):
                continue
            path = Path(ref)
            if path.is_absolute() or ".." in path.parts:
                failures.append(f"post_fcc_mem_015_021_context.absent_tracked_refs must use safe repo-relative paths: {ref}")
            elif (root / path).exists():
                failures.append(f"post_fcc_mem_015_021_context absent ref unexpectedly exists: {ref}")


def _validate_authority_boundary(payload: dict[str, Any], failures: list[str]) -> None:
    boundary = payload.get("authority_boundary")
    if not isinstance(boundary, dict):
        failures.append("authority_boundary must be an object")
        return
    for flag in REQUIRED_AUTHORITY_FLAGS:
        if boundary.get(flag) is not False:
            failures.append(f"authority_boundary.{flag} must be false")
    extra_flags = sorted(set(boundary) - set(REQUIRED_AUTHORITY_FLAGS))
    if extra_flags:
        failures.append(f"authority_boundary has unexpected flags: {', '.join(extra_flags)}")


def _validate_dimensions(payload: dict[str, Any], failures: list[str]) -> None:
    definitions = payload.get("dimension_definitions")
    if not isinstance(definitions, list):
        failures.append("dimension_definitions must be a list")
        return
    dimension_ids = [item.get("id") for item in definitions if isinstance(item, dict)]
    if tuple(dimension_ids) != REQUIRED_DIMENSIONS:
        failures.append("dimension_definitions must match the required deterministic dimension order")
    for item in definitions:
        if not isinstance(item, dict):
            failures.append("dimension_definitions entries must be objects")
            continue
        if item.get("max_score") != 5:
            failures.append(f"dimension {item.get('id', '<missing>')} max_score must be 5")
        _expect_non_empty_string(item.get("definition"), f"dimension {item.get('id', '<missing>')} definition", failures)


def _validate_module(module: dict[str, Any], root: Path, failures: list[str]) -> None:
    module_id = module.get("module_id")
    if not isinstance(module_id, str) or not module_id.strip():
        failures.append("module_id must be a non-empty string")
        return

    missing = sorted(REQUIRED_MODULE_FIELDS - set(module))
    if missing:
        failures.append(f"{module_id}: missing fields: {', '.join(missing)}")

    for field_name in (
        "module_name",
        "current_maturity",
        "next_checkpoint",
        "ranked_next_checkpoint",
        "recommended_next_task_ref",
        "prior_score_ref",
    ):
        _expect_non_empty_string(module.get(field_name), f"{module_id}.{field_name}", failures)

    score = module.get("current_maturity_score")
    if not isinstance(score, int) or not 0 <= score <= 6:
        failures.append(f"{module_id}.current_maturity_score must be an integer from 0 to 6")
    prior_score = module.get("prior_score")
    if not isinstance(prior_score, int) or not 0 <= prior_score <= 6:
        failures.append(f"{module_id}.prior_score must be an integer from 0 to 6")
    current_score = module.get("current_score")
    if not isinstance(current_score, int) or not 0 <= current_score <= 100:
        failures.append(f"{module_id}.current_score must be an integer from 0 to 100")
    prior_ref = module.get("prior_score_ref")
    if isinstance(prior_ref, str):
        failure = _validate_relative_existing_path(root, prior_ref, f"{module_id}.prior_score_ref")
        if failure:
            failures.append(failure)

    for field_name in MODULE_TEXT_LIST_FIELDS:
        _expect_non_empty_string_list(module.get(field_name), f"{module_id}.{field_name}", failures)

    for field_name in MODULE_REF_FIELDS:
        refs = module.get(field_name)
        _expect_non_empty_string_list(refs, f"{module_id}.{field_name}", failures)
        if isinstance(refs, list):
            for ref in refs:
                if isinstance(ref, str):
                    failure = _validate_relative_existing_path(root, ref, f"{module_id}.{field_name}")
                    if failure:
                        failures.append(failure)

    dimension_scores = module.get("dimension_scores")
    if not isinstance(dimension_scores, dict):
        failures.append(f"{module_id}.dimension_scores must be an object")
    else:
        if set(dimension_scores) != set(REQUIRED_DIMENSIONS):
            failures.append(f"{module_id}.dimension_scores must cover all required dimensions exactly")
        expected = _expected_composite(dimension_scores)
        if expected is None:
            failures.append(f"{module_id}.dimension_scores values must be integers from 0 to 5")
        elif module.get("composite_score") != expected:
            failures.append(
                f"{module_id}.composite_score {module.get('composite_score')} does not match expected {expected}"
            )
        elif module.get("current_score") != expected:
            failures.append(f"{module_id}.current_score {module.get('current_score')} does not match expected {expected}")

    composite = module.get("composite_score")
    if not isinstance(composite, int) or not 0 <= composite <= 100:
        failures.append(f"{module_id}.composite_score must be an integer from 0 to 100")


def _validate_modules(payload: dict[str, Any], root: Path, failures: list[str]) -> None:
    modules = payload.get("modules")
    if not isinstance(modules, list) or not modules:
        failures.append("modules must be a non-empty list")
        return
    ids: list[str] = []
    for module in modules:
        if not isinstance(module, dict):
            failures.append("module entries must be objects")
            continue
        module_id = module.get("module_id")
        if isinstance(module_id, str):
            ids.append(module_id)
        _validate_module(module, root, failures)
    if set(ids) != REQUIRED_MODULE_IDS:
        failures.append("modules must cover the required module ids exactly")
    duplicates = sorted({module_id for module_id in ids if ids.count(module_id) > 1})
    if duplicates:
        failures.append(f"duplicate module ids: {', '.join(duplicates)}")

    current_scores = [
        module.get("current_maturity_score")
        for module in modules
        if isinstance(module, dict) and isinstance(module.get("current_maturity_score"), int)
    ]
    composite_scores = [
        module.get("composite_score")
        for module in modules
        if isinstance(module, dict) and isinstance(module.get("composite_score"), int)
    ]
    summary = payload.get("summary_metrics")
    if not isinstance(summary, dict):
        failures.append("summary_metrics must be an object")
        summary = {}
    if summary.get("module_count") != len(modules):
        failures.append("summary_metrics.module_count must match module count")
    if current_scores:
        expected_average = round(sum(current_scores) / len(current_scores), 2)
        expected_benchmark_score = round((sum(current_scores) / (len(current_scores) * 6)) * 100)
        if summary.get("v1_average_maturity_score") != expected_average:
            failures.append("summary_metrics.v1_average_maturity_score must match current module scores")
        if summary.get("v1_benchmark_module_score") != expected_benchmark_score:
            failures.append("summary_metrics.v1_benchmark_module_score must match current benchmark formula")
    if composite_scores:
        expected_v2_average = round(sum(composite_scores) / len(composite_scores))
        if summary.get("v2_average_composite_score") != expected_v2_average:
            failures.append("summary_metrics.v2_average_composite_score must match composite scores")

    by_id = {module["module_id"]: module for module in modules if isinstance(module, dict) and isinstance(module.get("module_id"), str)}
    weak_ids = set(summary.get("weakest_module_ids", []))
    if not WEAK_MODULES <= weak_ids:
        failures.append("summary_metrics.weakest_module_ids must include decision_router and task_decomposition_module")
    if not WEAK_MODULES <= set(by_id):
        failures.append("weak modules are missing from module entries")
        return
    lowest_score = min(
        module.get("composite_score", 101)
        for module in by_id.values()
        if isinstance(module.get("composite_score"), int)
    )
    for weak_id in WEAK_MODULES:
        if by_id[weak_id].get("composite_score") != lowest_score:
            failures.append(f"{weak_id} must be one of the lowest composite-score modules")


def _validate_v1_alignment(payload: dict[str, Any], root: Path, failures: list[str]) -> None:
    source_ref = payload.get("source_maturity_map_ref")
    if not isinstance(source_ref, str) or not source_ref.strip():
        return
    source_path = root / source_ref
    if not source_path.exists():
        return
    try:
        v1_payload = _load_json(source_path)
    except ValueError as exc:
        failures.append(str(exc))
        return
    v1_modules = v1_payload.get("modules")
    v2_modules = payload.get("modules")
    if not isinstance(v1_modules, list) or not isinstance(v2_modules, list):
        return
    v1_by_id = {
        module["id"]: module
        for module in v1_modules
        if isinstance(module, dict) and isinstance(module.get("id"), str)
    }
    for module in v2_modules:
        if not isinstance(module, dict) or not isinstance(module.get("module_id"), str):
            continue
        module_id = module["module_id"]
        v1_module = v1_by_id.get(module_id)
        if not isinstance(v1_module, dict):
            continue
        if module.get("module_name") != v1_module.get("name"):
            failures.append(f"{module_id}.module_name must match V1 maturity map name")
        if module.get("current_maturity") != v1_module.get("maturity"):
            failures.append(f"{module_id}.current_maturity must match V1 maturity map maturity")
        if module.get("current_maturity_score") != v1_module.get("maturity_score"):
            failures.append(f"{module_id}.current_maturity_score must match V1 maturity map score")
        if module.get("prior_score") != v1_module.get("maturity_score"):
            failures.append(f"{module_id}.prior_score must match V1 maturity map score")
        if module.get("prior_score_ref") != payload.get("source_maturity_map_ref"):
            failures.append(f"{module_id}.prior_score_ref must match source_maturity_map_ref")


def _validate_ranked_queue(payload: dict[str, Any], root: Path, failures: list[str]) -> None:
    policy = payload.get("queued_prompt_execution_policy")
    if not isinstance(policy, dict):
        failures.append("queued_prompt_execution_policy must be an object")
    else:
        if policy.get("subagents_required") is not True:
            failures.append("queued_prompt_execution_policy.subagents_required must be true")
        roles = policy.get("default_subagent_roles")
        if not isinstance(roles, list) or len(roles) < 2:
            failures.append("queued_prompt_execution_policy.default_subagent_roles must list at least two roles")
        _expect_non_empty_string(policy.get("policy"), "queued_prompt_execution_policy.policy", failures)

    queue = payload.get("ranked_improvement_queue")
    if not isinstance(queue, list) or len(queue) < len(REQUIRED_QUEUE):
        failures.append("ranked_improvement_queue must include the required next work items")
        return
    task_refs = [item.get("task_ref") for item in queue if isinstance(item, dict)]
    if tuple(task_refs[: len(REQUIRED_QUEUE)]) != REQUIRED_QUEUE:
        failures.append("ranked_improvement_queue first items must be deterministic and in required order")
    ranks = [item.get("rank") for item in queue if isinstance(item, dict)]
    if ranks != list(range(1, len(queue) + 1)):
        failures.append("ranked_improvement_queue ranks must be consecutive from 1")
    for item in queue:
        if not isinstance(item, dict):
            failures.append("ranked_improvement_queue entries must be objects")
            continue
        task_ref = item.get("task_ref", "<missing>")
        for field_name in ("title", "priority", "scope", "rationale", "acceptance_checkpoint"):
            _expect_non_empty_string(item.get(field_name), f"{task_ref}.{field_name}", failures)
        targets = item.get("target_module_ids")
        if not isinstance(targets, list) or not targets:
            failures.append(f"{task_ref}.target_module_ids must be a non-empty list")
        else:
            for target in targets:
                if target not in REQUIRED_MODULE_IDS:
                    failures.append(f"{task_ref}.target_module_ids references unknown module: {target}")
        _expect_non_empty_string_list(item.get("blocked_authorities"), f"{task_ref}.blocked_authorities", failures)
        refs = item.get("evidence_refs")
        _expect_non_empty_string_list(refs, f"{task_ref}.evidence_refs", failures)
        review_plan = item.get("subagent_review_plan")
        _expect_non_empty_string_list(review_plan, f"{task_ref}.subagent_review_plan", failures)
        if isinstance(review_plan, list):
            joined_plan = " ".join(entry.lower() for entry in review_plan if isinstance(entry, str))
            if len(review_plan) < 2:
                failures.append(f"{task_ref}.subagent_review_plan must include at least two reviewers")
            if "repo-evidence" not in joined_plan:
                failures.append(f"{task_ref}.subagent_review_plan must include a repo-evidence reviewer")
            if "safety/product-language" not in joined_plan:
                failures.append(f"{task_ref}.subagent_review_plan must include a safety/product-language reviewer")
        if isinstance(refs, list):
            for ref in refs:
                if isinstance(ref, str):
                    failure = _validate_relative_existing_path(root, ref, f"{task_ref}.evidence_refs")
                    if failure:
                        failures.append(failure)


def _code_ref_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _code_ref_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _validate_no_new_runtime_authority(root: Path, failures: list[str]) -> None:
    for rel_path in TASK_OWNED_PYTHON_REFS:
        path = root / rel_path
        if not path.exists():
            failures.append(f"task-owned Python ref is missing: {rel_path.as_posix()}")
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            failures.append(f"{rel_path.as_posix()}: cannot parse Python source: {exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name.split(".")[0] for alias in node.names]
                elif node.module:
                    names = [node.module.split(".")[0]]
                for name in names:
                    if name in FORBIDDEN_IMPORT_ROOTS:
                        failures.append(f"{rel_path.as_posix()}: forbidden runtime authority import: {name}")
            if isinstance(node, ast.Call):
                call_name = _code_ref_name(node.func)
                call_root = call_name.split(".")[0]
                if call_name in FORBIDDEN_CALL_ROOTS or call_root in FORBIDDEN_CALL_ROOTS:
                    failures.append(f"{rel_path.as_posix()}: forbidden runtime authority call: {call_name}")


def _validate_no_positive_claims(root: Path, failures: list[str]) -> None:
    for rel_path in (REVIEW_JSON, REVIEW_MD):
        text = (root / rel_path).read_text(encoding="utf-8").lower()
        for claim in FORBIDDEN_POSITIVE_CLAIMS:
            if claim in text:
                failures.append(f"{rel_path.as_posix()} contains forbidden product-readiness claim: {claim}")


def verify_payload(payload: dict[str, Any], root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    if payload.get("schema_version") != REQUIRED_SCHEMA_VERSION:
        failures.append(f"schema_version must be {REQUIRED_SCHEMA_VERSION}")
    if payload.get("task_ref") != REQUIRED_TASK_REF:
        failures.append(f"task_ref must be {REQUIRED_TASK_REF}")
    for field_name in ("status", "baseline", "assessed_on", "review_scope", "composite_score_formula"):
        _expect_non_empty_string(payload.get(field_name), field_name, failures)
    source_ref = payload.get("source_maturity_map_ref")
    _expect_non_empty_string(source_ref, "source_maturity_map_ref", failures)
    if isinstance(source_ref, str):
        failure = _validate_relative_existing_path(root, source_ref, "source_maturity_map_ref")
        if failure:
            failures.append(failure)
    _validate_authority_boundary(payload, failures)
    _validate_post_mem_context(payload, root, failures)
    _validate_dimensions(payload, failures)
    _validate_modules(payload, root, failures)
    _validate_v1_alignment(payload, root, failures)
    _validate_ranked_queue(payload, root, failures)
    return failures


def verify(root: Path = ROOT, review_path: Path | None = None) -> list[str]:
    active_review_path = review_path or (root / REVIEW_JSON)
    failures = []
    if not (root / REVIEW_MD).exists():
        failures.append(f"missing review doc: {REVIEW_MD.as_posix()}")
    try:
        payload = _load_json(active_review_path)
    except ValueError as exc:
        return [str(exc)]
    failures.extend(verify_payload(payload, root))
    failures.extend(verify_v1_map(root))
    if (root / REVIEW_MD).exists():
        doc = (root / REVIEW_MD).read_text(encoding="utf-8")
        required_doc_fragments = (
            "UAA-P1-088 Agent Module Maturity Review V2",
            "UAA-P1-089 Top-Level Decision Router Contract",
            "UAA-P1-090 Task Decomposition Proposal Engine",
            "FCC-LOOP-002 Founder Loop Ergonomics Pass",
            "FCC-MEM-022 Ranked Retrieval / Recall Tuning",
            "FCC-MEM-015 through FCC-MEM-021",
            "product usefulness",
            "CLI parity",
            "decision_router",
            "task_decomposition_module",
            "does not add runtime model calls",
            "context injection",
        )
        for fragment in required_doc_fragments:
            if fragment not in doc:
                failures.append(f"review doc is missing required fragment: {fragment}")
    benchmark_text = (root / BENCHMARK_SCRIPT).read_text(encoding="utf-8") if (root / BENCHMARK_SCRIPT).exists() else ""
    for fragment in (
        REVIEW_JSON.as_posix(),
        REVIEW_MD.as_posix(),
        "scripts/verify_uaa_p1_088_agent_module_maturity_review_v2.py",
        "tests/test_uaa_p1_088_agent_module_maturity_review_v2.py",
    ):
        if fragment not in benchmark_text:
            failures.append(f"benchmark integration is missing V2 evidence ref: {fragment}")
    _validate_no_new_runtime_authority(root, failures)
    _validate_no_positive_claims(root, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify UAA-P1-088 Agent Module Maturity Review V2.")
    parser.add_argument(
        "--review",
        default=str(REVIEW_JSON),
        help="Repo-relative or absolute path to the V2 maturity review JSON.",
    )
    args = parser.parse_args(argv)
    review_path = Path(args.review)
    if not review_path.is_absolute():
        review_path = ROOT / review_path
    failures = verify(ROOT, review_path)
    if failures:
        print("FAIL: UAA-P1-088 Agent Module Maturity Review V2 verification failed")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("OK: UAA-P1-088 Agent Module Maturity Review V2 is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
