from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Protocol


CANONICAL_PYTEST_SHARD_COUNT = 8


class ShardPlanLike(Protocol):
    index: int
    files: tuple[str, ...]
    expected_seconds: float
    serialized_preflight: bool


def validate_shard_plans(
    files: list[str],
    plans: list[ShardPlanLike],
    shard_count: int,
    affinity_groups: list[tuple[str, ...]] | None = None,
    exclusive_affinity_groups: list[tuple[str, ...]] | None = None,
) -> None:
    if len(files) != len(set(files)):
        raise ValueError("pytest shard input contains duplicate test files")
    if [plan.index for plan in plans] != list(range(shard_count)):
        raise ValueError("pytest shard indices must be complete and ordered")
    assigned = [file_path for plan in plans for file_path in plan.files]
    if Counter(assigned) != Counter(files):
        raise ValueError("pytest shard plans must cover every test file exactly once")
    if any(tuple(sorted(plan.files)) != plan.files for plan in plans):
        raise ValueError("pytest shard files must use deterministic sorted order")
    if len(files) >= shard_count and any(not plan.files for plan in plans):
        raise ValueError("pytest shard plans may not contain avoidable empty shards")
    location = {
        file_path: plan.index for plan in plans for file_path in plan.files
    }
    for group in affinity_groups or []:
        if len({location.get(file_path) for file_path in group}) != 1:
            raise ValueError("pytest shard affinity group was split across shards")
    expected_exclusive = {
        tuple(sorted(set(group))) for group in (exclusive_affinity_groups or [])
    }
    actual_exclusive = {
        tuple(plan.files) for plan in plans if plan.serialized_preflight
    }
    if actual_exclusive != expected_exclusive:
        raise ValueError(
            "pytest serialized preflight plans must exactly match exclusive groups"
        )
    for plan in plans:
        if plan.serialized_preflight and not plan.files:
            raise ValueError("pytest serialized preflight plan may not be empty")


def shard_plan_fingerprint(plans: list[ShardPlanLike]) -> str:
    payload = [
        {
            "index": plan.index,
            "files": list(plan.files),
            "expected_seconds": plan.expected_seconds,
            "serialized_preflight": plan.serialized_preflight,
        }
        for plan in plans
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f"pytest-shard-plan-ref:sha256:{hashlib.sha256(encoded).hexdigest()}"
