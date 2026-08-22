from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


STATIC_TIMING_SCHEMA = "verify_all_timings.v1"
STATIC_PLAN_SCHEMA = "uaa-static-scan-plan.v1"
STATIC_REGISTRY_SCHEMA = "uaa-static-scan-registry.v1"
DEFAULT_SCAN_MILLISECONDS = 100.0
# This fingerprint approves only the exact current-main registry for parallel
# execution. A new or renamed scan fails closed into the serial lane until the
# registry is reviewed and this value is intentionally updated.
APPROVED_PARALLEL_REGISTRY_FINGERPRINT = (
    "static-registry-ref:sha256:"
    "c4584384a1b92731482ece829d2b7c7e2a7257b4ae7bbae1a57b72fbaa32b683"
)
EXCLUSIVE_SCAN_FUNCTIONS = frozenset(
    {
        "verify_no_generated_artifacts",
        "verify_operational_maturity",
        "verify_repo_awareness_benchmark",
        "verify_backup_restore_verification",
    }
)
API_AFFINITY_FUNCTIONS = frozenset(
    {
        "verify_uaa_p1_080_api_route_classification",
        "verify_uaa_p1_081_fastapi_security_headers",
        "verify_uaa_p1_082_loopback_cors",
        "verify_uaa_p1_083_local_auth_gate",
        "verify_uaa_p1_084_mutating_route_idempotency",
        "verify_uaa_p1_085_targeted_rate_limits",
        "verify_uaa_p1_086_api_boundary_enforcement_tests",
    }
)
PRODUCT_AFFINITY_FUNCTIONS = frozenset(
    {
        "verify_control_center_release_surface",
        "verify_control_center_capability_surface",
        "verify_fcc_v1_001_api_perimeter",
        "verify_fcc_v1_002_action_inbox_state_machine",
        "verify_fcc_v1_003_founder_loop_vertical_slice",
        "verify_fcc_v1_004_chat_durable_receipt_handoff",
        "verify_fcc_v1_005_memory_review_decisions",
        "verify_governed_cognitive_memory_spine_v1",
        "verify_fcc_v1_006_evidence_timeline_productization",
        "verify_founder_loop_v1",
        "verify_product_vision_registry",
    }
)


@dataclass(frozen=True)
class StaticScanSpec:
    index: int
    name: str
    function_name: str
    execution_class: str
    affinity_ref: str | None = None

    @property
    def scan_ref(self) -> str:
        return f"static-scan-ref:{self.index:03d}"


@dataclass(frozen=True)
class StaticShardPlan:
    index: int
    scans: tuple[StaticScanSpec, ...]
    expected_milliseconds: float
    execution_class: str = "parallel_safe"


def build_scan_specs(
    sequence: Iterable[tuple[str, str]],
    *,
    approved_parallel_registry_fingerprint: str = (
        APPROVED_PARALLEL_REGISTRY_FINGERPRINT
    ),
) -> tuple[StaticScanSpec, ...]:
    sequence_items = tuple(sequence)
    parallel_registry_approved = (
        scan_registry_fingerprint(sequence_items)
        == approved_parallel_registry_fingerprint
    )
    specs: list[StaticScanSpec] = []
    names: set[str] = set()
    functions: set[str] = set()
    for index, (name, function_name) in enumerate(sequence_items):
        if not name or not function_name:
            raise ValueError("static scan names and function names must be non-empty")
        if name in names:
            raise ValueError(f"duplicate static scan name: {name}")
        if function_name in functions:
            raise ValueError(f"duplicate static scan function: {function_name}")
        names.add(name)
        functions.add(function_name)
        specs.append(
            StaticScanSpec(
                index=index,
                name=name,
                function_name=function_name,
                execution_class=(
                    "exclusive"
                    if (
                        function_name in EXCLUSIVE_SCAN_FUNCTIONS
                        or not parallel_registry_approved
                    )
                    else "parallel_safe"
                ),
                affinity_ref=(
                    "affinity-ref:product-verification"
                    if function_name in PRODUCT_AFFINITY_FUNCTIONS
                    else (
                        "affinity-ref:api-perimeter"
                        if function_name in API_AFFINITY_FUNCTIONS
                        else None
                    )
                ),
            )
        )
    if not specs:
        raise ValueError("static scan registry must not be empty")
    return tuple(specs)


def scan_registry_fingerprint(sequence: Iterable[tuple[str, str]]) -> str:
    projection = {
        "schema_version": STATIC_REGISTRY_SCHEMA,
        "scans": [
            {"name": name, "function_name": function_name}
            for name, function_name in sequence
        ],
    }
    encoded = json.dumps(projection, separators=(",", ":"), sort_keys=True).encode()
    return f"static-registry-ref:sha256:{hashlib.sha256(encoded).hexdigest()}"


def load_static_timings(
    path: Path | None,
    specs: tuple[StaticScanSpec, ...],
) -> dict[str, float]:
    if path is None or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    if payload.get("schema_version") != STATIC_TIMING_SCHEMA:
        return {}
    raw_timings = payload.get("timings")
    if not isinstance(raw_timings, list):
        return {}
    known = {f"static_scan:{spec.name}": spec.function_name for spec in specs}
    timings: dict[str, float] = {}
    for item in raw_timings:
        if not isinstance(item, dict) or item.get("name") not in known:
            continue
        elapsed = item.get("elapsed_ms")
        if isinstance(elapsed, (int, float)) and elapsed >= 0:
            timings[known[str(item["name"])]] = max(float(elapsed), 1.0)
    return timings


def _assignment_items(
    specs: tuple[StaticScanSpec, ...],
) -> list[tuple[StaticScanSpec, ...]]:
    grouped: dict[str, list[StaticScanSpec]] = {}
    standalone: list[tuple[StaticScanSpec, ...]] = []
    for spec in specs:
        if spec.affinity_ref is None:
            standalone.append((spec,))
        else:
            grouped.setdefault(spec.affinity_ref, []).append(spec)
    standalone.extend(tuple(group) for _, group in sorted(grouped.items()))
    return standalone


def assign_static_shards(
    specs: tuple[StaticScanSpec, ...],
    worker_count: int,
    timings: dict[str, float] | None = None,
    *,
    shuffle_seed: int | None = None,
) -> tuple[StaticShardPlan, ...]:
    if worker_count <= 0:
        raise ValueError("static scan worker count must be greater than zero")
    parallel_specs = tuple(
        spec for spec in specs if spec.execution_class == "parallel_safe"
    )
    if not parallel_specs:
        return ()
    count = min(worker_count, len(parallel_specs))
    values = timings or {}
    items = _assignment_items(parallel_specs)
    items.sort(
        key=lambda item: (
            -sum(
                values.get(spec.function_name, DEFAULT_SCAN_MILLISECONDS)
                for spec in item
            ),
            item[0].index,
        )
    )
    shard_scans: list[list[StaticScanSpec]] = [[] for _ in range(count)]
    shard_totals = [0.0 for _ in range(count)]
    for item in items:
        shard_index = min(
            range(count),
            key=lambda index: (shard_totals[index], len(shard_scans[index]), index),
        )
        shard_scans[shard_index].extend(item)
        shard_totals[shard_index] += sum(
            values.get(spec.function_name, DEFAULT_SCAN_MILLISECONDS) for spec in item
        )
    randomizer = random.Random(shuffle_seed) if shuffle_seed is not None else None
    plans: list[StaticShardPlan] = []
    for index in range(count):
        scans = sorted(shard_scans[index], key=lambda spec: spec.index)
        if randomizer is not None:
            randomizer.shuffle(scans)
        plans.append(
            StaticShardPlan(
                index=index,
                scans=tuple(scans),
                expected_milliseconds=round(shard_totals[index], 3),
            )
        )
    return tuple(plans)


def exclusive_plans(specs: tuple[StaticScanSpec, ...]) -> tuple[StaticShardPlan, ...]:
    exclusive_specs = tuple(
        spec for spec in specs if spec.execution_class != "parallel_safe"
    )
    if not exclusive_specs:
        return ()
    return (
        StaticShardPlan(
            index=0,
            scans=exclusive_specs,
            expected_milliseconds=DEFAULT_SCAN_MILLISECONDS * len(exclusive_specs),
            execution_class="exclusive",
        ),
    )


def plan_fingerprint(
    plans: Iterable[StaticShardPlan],
    *,
    repository_sha: str | None = None,
    registry_fingerprint: str | None = None,
) -> str:
    projection = {
        "repository_sha": repository_sha,
        "registry_fingerprint": registry_fingerprint,
        "shards": [
            {
                "execution_class": plan.execution_class,
                "index": plan.index,
                "scan_refs": [spec.scan_ref for spec in plan.scans],
            }
            for plan in plans
        ],
    }
    encoded = json.dumps(projection, separators=(",", ":"), sort_keys=True).encode()
    return f"static-plan-ref:sha256:{hashlib.sha256(encoded).hexdigest()}"
