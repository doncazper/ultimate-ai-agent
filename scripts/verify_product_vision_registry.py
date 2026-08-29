#!/usr/bin/env python3
"""Verify the Queue V2 product vision preservation layer."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/roadmap/UAA_PRODUCT_VISION_REGISTRY.json"
QUEUE = ROOT / "docs/roadmap/UAA_DEVELOPER_QUEUE_V2_MANIFEST.json"
EXPECTED_SCHEMA = "uaa.product_vision_registry.v2"
EXPECTED_STATUS = "canonical_vision_preservation_layer"
ALLOWED_STRENGTHS = {"strong", "adequate", "recovered", "reconstructed"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ALLOWED_WHOLE_STATUSES = {"planned", "partial", "blocked", "complete"}
QUEUE_COVERAGE_MARKER = "queue_item_dispositions"
REQUIRED_COVERAGE_VALUE = "required"
ALLOWED_COVERAGE_VALUES = {REQUIRED_COVERAGE_VALUE, "not_required"}
DETAIL_PLAN_PREFIXES = ("docs/implementation/", "docs/evals/")
SHA256_RE = re.compile(r"[0-9a-f]{64}")


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
    if coverage.get("queue_item_marker") != QUEUE_COVERAGE_MARKER:
        failures.append("vision registry queue coverage marker drifted")
    if coverage.get("required_marker_value") != REQUIRED_COVERAGE_VALUE:
        failures.append("vision registry required marker value drifted")
    if not _nonempty_text(coverage.get("expansion_rule")):
        failures.append("vision registry expansion rule is missing")
    if not _nonempty_text(coverage.get("completion_rule")):
        failures.append("whole-vision completion rule is missing")

    queue_items_raw = queue_payload.get("items")
    if not isinstance(queue_items_raw, list):
        return [*failures, "Queue V2 items are missing"]
    queue_item_ids = [
        item.get("item_id")
        for item in queue_items_raw
        if isinstance(item, dict) and isinstance(item.get("item_id"), str)
    ]
    if len(queue_item_ids) != len(set(queue_item_ids)):
        failures.append("Queue V2 item IDs are duplicated")
    queue_items = {
        item["item_id"]: item
        for item in queue_items_raw
        if isinstance(item, dict) and isinstance(item.get("item_id"), str)
    }
    dispositions = payload.get(QUEUE_COVERAGE_MARKER)
    if not isinstance(dispositions, dict):
        failures.append("Queue V2 vision registry dispositions are missing")
        dispositions = {}
    if set(dispositions) != set(queue_items):
        failures.append("Queue V2 vision registry dispositions are incomplete or extra")
    required_ids: set[str] = set()
    for queue_id, disposition in dispositions.items():
        if disposition not in ALLOWED_COVERAGE_VALUES:
            failures.append(
                f"{queue_id}: Queue V2 vision registry disposition is missing or invalid"
            )
        elif disposition == REQUIRED_COVERAGE_VALUE:
            required_ids.add(queue_id)

    evidence_catalog = payload.get("completion_evidence_catalog")
    if not isinstance(evidence_catalog, dict):
        failures.append("completion evidence catalog is missing")
        evidence_catalog = {}
    for evidence_ref, binding in evidence_catalog.items():
        evidence_prefix = f"completion evidence {evidence_ref}: "
        if not _nonempty_text(evidence_ref) or not str(evidence_ref).startswith(
            "evidence-ref:"
        ):
            failures.append("completion evidence catalog contains an invalid ref")
            continue
        if not isinstance(binding, dict):
            failures.append(evidence_prefix + "binding is missing")
            continue
        if binding.get("item_id") not in required_ids:
            failures.append(evidence_prefix + "item binding is invalid")
        artifact_path = binding.get("artifact_path")
        artifact_sha256 = binding.get("artifact_sha256")
        if not _nonempty_text(artifact_path):
            failures.append(evidence_prefix + "artifact path is missing")
        if not isinstance(artifact_sha256, str) or not SHA256_RE.fullmatch(
            artifact_sha256
        ):
            failures.append(evidence_prefix + "artifact digest is invalid")
        if not _nonempty_text(binding.get("independent_verifier_ref")) or not str(
            binding.get("independent_verifier_ref", "")
        ).startswith("verifier-ref:"):
            failures.append(evidence_prefix + "independent verifier ref is invalid")
        if not _nonempty_text(binding.get("verification_receipt_ref")) or not str(
            binding.get("verification_receipt_ref", "")
        ).startswith("verification-receipt-ref:"):
            failures.append(evidence_prefix + "verification receipt ref is invalid")
        if check_refs and _nonempty_text(artifact_path):
            if not _safe_repo_file(root, artifact_path):
                failures.append(evidence_prefix + "artifact path is unsafe or missing")
            elif isinstance(artifact_sha256, str) and SHA256_RE.fullmatch(
                artifact_sha256
            ):
                artifact = root.joinpath(*PurePosixPath(artifact_path).parts)
                actual_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
                if actual_digest != artifact_sha256:
                    failures.append(evidence_prefix + "artifact digest mismatched")

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
    if registry_ids != required_ids:
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
        source_bindings = item.get("queue_source_bindings")
        if not isinstance(source_bindings, dict):
            failures.append(prefix + "queue source bindings are missing")
            source_bindings = {}
        if set(source_bindings) != declared_ref_set:
            failures.append(prefix + "queue source binding keys are unresolved")
        if isinstance(queue_item, dict):
            queue_refs = queue_item.get("source_refs")
            queue_ref_set = (
                {
                    ref
                    for ref in queue_refs
                    if not ref.startswith("legacy-source-acceptance-ref:")
                }
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
        unresolved_completion_refs = [
            ref
            for ref in completion_refs
            if ref not in evidence_catalog
            or not isinstance(evidence_catalog.get(ref), dict)
            or evidence_catalog[ref].get("item_id") != item_id
        ]
        if unresolved_completion_refs:
            failures.append(prefix + "completion evidence refs are unresolved")
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
        for source_ref, bound_paths in source_bindings.items():
            if not _nonempty_text_list(bound_paths):
                failures.append(prefix + f"source binding is empty: {source_ref}")
                continue
            if len(bound_paths) != len(set(bound_paths)):
                failures.append(prefix + f"source binding is duplicated: {source_ref}")
            for bound_path in bound_paths:
                if bound_path not in canonical_paths:
                    failures.append(
                        prefix + f"source binding target is not canonical: {source_ref}"
                    )
                elif check_refs and not _safe_repo_file(root, bound_path):
                    failures.append(
                        prefix + f"source binding target is unsafe or missing: {source_ref}"
                    )

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
