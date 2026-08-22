#!/usr/bin/env python3
"""Verify the Queue V2 product vision preservation layer."""

from __future__ import annotations

import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/roadmap/UAA_PRODUCT_VISION_REGISTRY.json"
QUEUE = ROOT / "docs/roadmap/UAA_DEVELOPER_QUEUE_V2_MANIFEST.json"
EXPECTED_SCHEMA = "uaa.product_vision_registry.v1"
EXPECTED_STATUS = "canonical_vision_preservation_layer"
ALLOWED_STRENGTHS = {"strong", "adequate", "recovered", "reconstructed"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ALLOWED_WHOLE_STATUSES = {"planned", "partial", "blocked", "complete"}
REQUIRED_PRODUCT_ITEMS = {
    "Q15",
    "Q24",
    "Q25",
    "Q26",
    "Q27",
    "Q28",
    "Q29",
    "Q30",
    "Q31",
}
DETAIL_PLAN_PREFIXES = ("docs/implementation/", "docs/evals/")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonempty_text_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(_nonempty_text(item) for item in value)
    )


def _safe_repo_file(root: Path, ref: Any) -> bool:
    if not _nonempty_text(ref):
        return False
    path_ref = str(ref)
    pure = PurePosixPath(path_ref)
    if pure.is_absolute() or path_ref != pure.as_posix():
        return False
    if not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        return False
    candidate = root.joinpath(*pure.parts)
    cursor = root
    for part in pure.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return False
    try:
        resolved_root = root.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
    except OSError:
        return False
    if candidate.is_symlink() or not candidate.is_file():
        return False
    return resolved.is_relative_to(resolved_root)


def verify(
    *,
    payload: dict[str, Any] | None = None,
    queue_payload: dict[str, Any] | None = None,
    root: Path = ROOT,
    check_refs: bool = True,
) -> list[str]:
    failures: list[str] = []
    if payload is None:
        try:
            payload = _load_json(root / REGISTRY.relative_to(ROOT))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            return [f"product vision registry is unreadable: {exc}"]
    if queue_payload is None:
        try:
            queue_payload = _load_json(root / QUEUE.relative_to(ROOT))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            return [f"Queue V2 manifest is unreadable: {exc}"]

    if payload.get("schema_version") != EXPECTED_SCHEMA:
        failures.append("product vision registry schema drifted")
    if payload.get("artifact_status") != EXPECTED_STATUS:
        failures.append("product vision registry artifact status drifted")
    if not _nonempty_text(payload.get("purpose")):
        failures.append("product vision registry purpose is missing")
    if not _nonempty_text_list(payload.get("assistant_os_invariants")):
        failures.append("assistant OS invariants are missing")

    coverage = payload.get("coverage_policy")
    if not isinstance(coverage, dict):
        failures.append("coverage policy is missing")
        coverage = {}
    required_ids_raw = coverage.get("required_queue_item_ids")
    required_ids = (
        set(required_ids_raw)
        if isinstance(required_ids_raw, list)
        and all(isinstance(item, str) for item in required_ids_raw)
        else set()
    )
    if required_ids != REQUIRED_PRODUCT_ITEMS:
        failures.append("required product queue item coverage drifted")
    if isinstance(required_ids_raw, list) and len(required_ids_raw) != len(required_ids):
        failures.append("required product queue item coverage is duplicated")
    if not _nonempty_text(coverage.get("expansion_rule")):
        failures.append("vision registry expansion rule is missing")
    if not _nonempty_text(coverage.get("completion_rule")):
        failures.append("whole-vision completion rule is missing")

    queue_items_raw = queue_payload.get("items")
    if not isinstance(queue_items_raw, list):
        return [*failures, "Queue V2 items are missing"]
    queue_items = {
        item.get("item_id"): item
        for item in queue_items_raw
        if isinstance(item, dict) and isinstance(item.get("item_id"), str)
    }
    missing_queue_ids = sorted(REQUIRED_PRODUCT_ITEMS - set(queue_items))
    if missing_queue_ids:
        failures.append(
            "required product items are absent from Queue V2: "
            + ", ".join(missing_queue_ids)
        )

    registry_items_raw = payload.get("items")
    if not isinstance(registry_items_raw, list):
        return [*failures, "product vision registry items are missing"]
    item_ids = [
        item.get("item_id")
        for item in registry_items_raw
        if isinstance(item, dict)
    ]
    if len(item_ids) != len(set(item_ids)):
        failures.append("product vision registry item IDs are duplicated")
    registry_ids = {item for item in item_ids if isinstance(item, str)}
    if registry_ids != REQUIRED_PRODUCT_ITEMS:
        failures.append("product vision registry item set is incomplete or extra")

    for item in registry_items_raw:
        if not isinstance(item, dict):
            failures.append("product vision registry contains a non-object item")
            continue
        item_id = item.get("item_id")
        if not isinstance(item_id, str):
            failures.append("product vision registry item lacks an item_id")
            continue
        prefix = f"{item_id}: "
        if not _nonempty_text(item.get("title")):
            failures.append(prefix + "title is missing")
        if item.get("vision_strength") not in ALLOWED_STRENGTHS:
            failures.append(prefix + "vision strength is invalid")
        if item.get("source_confidence") not in ALLOWED_CONFIDENCE:
            failures.append(prefix + "source confidence is invalid")

        queue_item = queue_items.get(item_id)
        declared_refs = item.get("queue_source_refs")
        if not _nonempty_text_list(declared_refs):
            failures.append(prefix + "queue source refs are missing")
            declared_ref_set: set[str] = set()
        else:
            declared_ref_set = set(declared_refs)
        if isinstance(queue_item, dict):
            queue_refs = queue_item.get("source_refs")
            queue_ref_set = (
                set(queue_refs)
                if isinstance(queue_refs, list)
                and all(isinstance(ref, str) for ref in queue_refs)
                else set()
            )
            if declared_ref_set != queue_ref_set:
                failures.append(prefix + "symbolic Queue V2 source refs are unresolved")

        current_slice = item.get("current_slice")
        whole_vision = item.get("whole_vision")
        if not isinstance(current_slice, dict):
            failures.append(prefix + "current slice is missing")
            current_slice = {}
        if not isinstance(whole_vision, dict):
            failures.append(prefix + "whole vision is missing")
            whole_vision = {}
        for field in ("name", "scope_status", "outcome"):
            if not _nonempty_text(current_slice.get(field)):
                failures.append(prefix + f"current slice {field} is missing")
        if whole_vision.get("status") not in ALLOWED_WHOLE_STATUSES:
            failures.append(prefix + "whole-vision status is invalid")
        if not _nonempty_text(whole_vision.get("outcome")):
            failures.append(prefix + "whole-vision outcome is missing")
        if not _nonempty_text_list(whole_vision.get("future_stages")):
            failures.append(prefix + "whole-vision future stages are missing")
        completion_refs = whole_vision.get("completion_evidence_refs")
        if not isinstance(completion_refs, list) or not all(
            _nonempty_text(ref) for ref in completion_refs
        ):
            failures.append(prefix + "completion evidence refs are invalid")
            completion_refs = []
        if whole_vision.get("status") == "complete" and not completion_refs:
            failures.append(prefix + "whole vision is complete without evidence")
        if (
            _nonempty_text(current_slice.get("outcome"))
            and current_slice.get("outcome") == whole_vision.get("outcome")
        ):
            failures.append(prefix + "current slice is conflated with whole vision")

        canonical_paths = item.get("canonical_source_paths")
        if not _nonempty_text_list(canonical_paths):
            failures.append(prefix + "canonical source paths are missing")
            canonical_paths = []
        if len(canonical_paths) != len(set(canonical_paths)):
            failures.append(prefix + "canonical source paths are duplicated")
        if check_refs:
            for ref in canonical_paths:
                if not _safe_repo_file(root, ref):
                    failures.append(prefix + f"canonical source path is unsafe or missing: {ref}")

        historical_refs = item.get("historical_source_refs")
        if not isinstance(historical_refs, list) or not all(
            _nonempty_text(ref) and str(ref).startswith("codex-thread-ref:")
            for ref in historical_refs
        ):
            failures.append(prefix + "historical source refs are invalid")
            historical_refs = []
        strength = item.get("vision_strength")
        if strength == "recovered" and not historical_refs:
            failures.append(prefix + "recovered vision lacks archived provenance")
        if strength in {"recovered", "reconstructed"}:
            if not _nonempty_text(item.get("recovery_note")):
                failures.append(prefix + "recovery note is missing")
            if not any(str(ref).startswith(DETAIL_PLAN_PREFIXES) for ref in canonical_paths):
                failures.append(prefix + "recovered vision lacks a detailed plan")

        if not _nonempty_text_list(item.get("guardrail_refs")):
            failures.append(prefix + "guardrail refs are missing")
        if not _nonempty_text(item.get("recovery_note")):
            failures.append(prefix + "recovery explanation is missing")

    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(
        "OK: Product vision registry preserves Queue V2 slices, whole visions, "
        "and resolvable sources"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
