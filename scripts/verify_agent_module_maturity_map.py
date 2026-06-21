#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MAP = Path("docs/registry/agent_module_maturity_map.json")

REQUIRED_MODULE_IDS = {
    "agent_runtime_skeleton",
    "orchestration_layer",
    "decision_router",
    "planning_module",
    "task_decomposition_module",
    "workflow_engine",
    "state_manager",
    "context_manager",
    "memory_module",
    "tool_registry",
    "capability_registry",
    "multi_agent_coordinator",
    "human_in_the_loop",
}

REQUIRED_MODULE_FIELDS = {
    "id",
    "name",
    "requested_definition",
    "status",
    "maturity",
    "maturity_score",
    "summary",
    "primary_paths",
    "supporting_paths",
    "test_paths",
    "evidence",
    "gaps",
    "next_checkpoint",
}

PATH_FIELDS = ("primary_paths", "supporting_paths", "test_paths")
LIST_TEXT_FIELDS = ("evidence", "gaps")


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


def verify_payload(payload: dict[str, Any], root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    if payload.get("schema_version") != 1:
        failures.append("schema_version must be 1")
    for field_name in ("baseline", "assessed_on", "assessment_scope"):
        if not isinstance(payload.get(field_name), str) or not payload[field_name].strip():
            failures.append(f"{field_name} must be a non-empty string")

    maturity_levels = payload.get("maturity_levels")
    if not isinstance(maturity_levels, list) or not maturity_levels:
        failures.append("maturity_levels must be a non-empty list")
        maturity_by_id: dict[str, int] = {}
    else:
        maturity_by_id = {}
        seen_scores: set[int] = set()
        for level in maturity_levels:
            if not isinstance(level, dict):
                failures.append("each maturity level must be an object")
                continue
            level_id = level.get("id")
            score = level.get("score")
            if not isinstance(level_id, str) or not level_id:
                failures.append("maturity level id must be a non-empty string")
            if not isinstance(score, int) or score < 0:
                failures.append(f"maturity level {level_id or '<missing>'} score must be a non-negative integer")
            if isinstance(level_id, str) and isinstance(score, int):
                if level_id in maturity_by_id:
                    failures.append(f"duplicate maturity level id: {level_id}")
                if score in seen_scores:
                    failures.append(f"duplicate maturity level score: {score}")
                maturity_by_id[level_id] = score
                seen_scores.add(score)
            if not isinstance(level.get("definition"), str) or not level["definition"].strip():
                failures.append(f"maturity level {level_id or '<missing>'} must define its meaning")

    modules = payload.get("modules")
    if not isinstance(modules, list):
        failures.append("modules must be a list")
        return failures

    module_ids: list[str] = []
    for module in modules:
        if not isinstance(module, dict):
            failures.append("each module must be an object")
            continue
        module_id = module.get("id")
        if not isinstance(module_id, str) or not module_id:
            failures.append("module id must be a non-empty string")
            continue
        module_ids.append(module_id)
        missing_fields = sorted(REQUIRED_MODULE_FIELDS - module.keys())
        if missing_fields:
            failures.append(f"{module_id}: missing fields: {', '.join(missing_fields)}")

        for field_name in REQUIRED_MODULE_FIELDS - set(PATH_FIELDS) - set(LIST_TEXT_FIELDS):
            value = module.get(field_name)
            if field_name == "maturity_score":
                if not isinstance(value, int):
                    failures.append(f"{module_id}: maturity_score must be an integer")
                continue
            if not isinstance(value, str) or not value.strip():
                failures.append(f"{module_id}: {field_name} must be a non-empty string")

        maturity = module.get("maturity")
        score = module.get("maturity_score")
        if isinstance(maturity, str) and maturity not in maturity_by_id:
            failures.append(f"{module_id}: unknown maturity level: {maturity}")
        elif isinstance(maturity, str) and isinstance(score, int) and maturity_by_id.get(maturity) != score:
            failures.append(
                f"{module_id}: maturity_score {score} does not match maturity "
                f"{maturity} score {maturity_by_id.get(maturity)}"
            )

        for field_name in PATH_FIELDS:
            values = module.get(field_name)
            if not isinstance(values, list) or not values:
                failures.append(f"{module_id}: {field_name} must be a non-empty list")
                continue
            for rel_path in values:
                if not isinstance(rel_path, str) or not rel_path.strip():
                    failures.append(f"{module_id}: {field_name} entries must be non-empty strings")
                    continue
                failure = _validate_relative_existing_path(root, rel_path, f"{module_id}.{field_name}")
                if failure:
                    failures.append(failure)

        for field_name in LIST_TEXT_FIELDS:
            values = module.get(field_name)
            if not isinstance(values, list) or not values:
                failures.append(f"{module_id}: {field_name} must be a non-empty list")
                continue
            for value in values:
                if not isinstance(value, str) or not value.strip():
                    failures.append(f"{module_id}: {field_name} entries must be non-empty strings")

    seen_module_ids = set(module_ids)
    duplicate_ids = sorted({module_id for module_id in module_ids if module_ids.count(module_id) > 1})
    if duplicate_ids:
        failures.append(f"duplicate module ids: {', '.join(duplicate_ids)}")
    missing_ids = sorted(REQUIRED_MODULE_IDS - seen_module_ids)
    if missing_ids:
        failures.append(f"missing requested module ids: {', '.join(missing_ids)}")
    unexpected_ids = sorted(seen_module_ids - REQUIRED_MODULE_IDS)
    if unexpected_ids:
        failures.append(f"unexpected module ids: {', '.join(unexpected_ids)}")

    return failures


def verify(root: Path = ROOT, map_path: Path | None = None) -> list[str]:
    active_map_path = map_path or (root / DEFAULT_MAP)
    try:
        payload = _load_json(active_map_path)
    except ValueError as exc:
        return [str(exc)]
    return verify_payload(payload, root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the UAA agent module maturity map.")
    parser.add_argument(
        "--map",
        default=str(DEFAULT_MAP),
        help="Repo-relative or absolute path to the module maturity map JSON.",
    )
    args = parser.parse_args(argv)
    map_path = Path(args.map)
    if not map_path.is_absolute():
        map_path = ROOT / map_path
    failures = verify(ROOT, map_path)
    if failures:
        print("FAIL: agent module maturity map verification failed")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("OK: agent module maturity map is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
