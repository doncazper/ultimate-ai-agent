#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.verification import run_all_legacy as legacy  # noqa: E402
from scripts.verification.static_scan_context import (  # noqa: E402
    DIRECT_PRODUCT_VALIDATORS,
    ProductVerificationSnapshot,
    StaticVerificationContext,
    resolve_repository_sha,
)
from scripts.verification.static_scan_plan import (  # noqa: E402
    STATIC_PLAN_SCHEMA,
    build_scan_specs,
    scan_registry_fingerprint,
)


RESULT_SCHEMA = "uaa-static-scan-worker-result.v1"
PROGRESS_SCHEMA = "uaa-static-scan-worker-progress.v1"


@dataclass(frozen=True)
class StaticWorkerPlan:
    scan_indices: tuple[int, ...]
    repository_sha: str
    registry_fingerprint: str
    context_ref: str


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("static scan worker plan must be an object")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(8)}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(temp_path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    temp_path.replace(path)


def _load_plan(path: Path) -> StaticWorkerPlan:
    payload = _read_json(path)
    if payload.get("schema_version") != STATIC_PLAN_SCHEMA:
        raise ValueError("static scan worker plan schema is unsupported")
    raw_indices = payload.get("scan_indices")
    if not isinstance(raw_indices, list) or not raw_indices:
        raise ValueError("static scan worker plan must contain scan indices")
    if any(not isinstance(index, int) or index < 0 for index in raw_indices):
        raise ValueError("static scan worker plan contains an invalid scan index")
    indices = tuple(raw_indices)
    if len(indices) != len(set(indices)):
        raise ValueError("static scan worker plan repeats a scan index")
    repository_sha = payload.get("repository_sha")
    registry_fingerprint = payload.get("registry_fingerprint")
    context_ref = payload.get("context_ref")
    if not isinstance(repository_sha, str):
        raise ValueError("static scan worker plan omits repository identity")
    if not isinstance(registry_fingerprint, str):
        raise ValueError("static scan worker plan omits registry identity")
    if not isinstance(context_ref, str):
        raise ValueError("static scan worker plan omits context identity")
    return StaticWorkerPlan(
        scan_indices=indices,
        repository_sha=repository_sha,
        registry_fingerprint=registry_fingerprint,
        context_ref=context_ref,
    )


def run_worker(
    plan_path: Path,
    result_path: Path,
    progress_path: Path,
) -> int:
    specs = build_scan_specs(legacy.SCAN_SEQUENCE)
    specs_by_index = {spec.index: spec for spec in specs}
    plan = _load_plan(plan_path)
    registry_fingerprint = scan_registry_fingerprint(legacy.SCAN_SEQUENCE)
    if registry_fingerprint != plan.registry_fingerprint:
        raise ValueError("static scan worker registry identity mismatch")
    if resolve_repository_sha(ROOT) != plan.repository_sha:
        raise ValueError("static scan worker repository identity mismatch")
    if any(index not in specs_by_index for index in plan.scan_indices):
        raise ValueError("static scan worker plan references an unknown scan")
    selected = tuple(specs_by_index[index] for index in plan.scan_indices)
    context = StaticVerificationContext.capture(
        ROOT,
        tuple(spec.scan_ref for spec in selected),
        plan.repository_sha,
        plan.registry_fingerprint,
    )
    if context.snapshot_ref != plan.context_ref:
        raise ValueError("static scan worker context identity mismatch")
    outcomes: list[dict[str, Any]] = []
    result_payload = {
        "schema_version": RESULT_SCHEMA,
        "context_ref": context.snapshot_ref,
        "registry_fingerprint": context.registry_fingerprint,
        "repository_sha": context.repository_sha,
        "outcomes": outcomes,
    }
    _write_json(result_path, result_payload)
    with context.cached_repository_view():
        product_snapshot = (
            ProductVerificationSnapshot.capture(ROOT)
            if any(spec.function_name in DIRECT_PRODUCT_VALIDATORS for spec in selected)
            else None
        )
        for spec in selected:
            _write_json(
                progress_path,
                {
                    "schema_version": PROGRESS_SCHEMA,
                    "state": "running",
                    "scan_index": spec.index,
                    "scan_ref": spec.scan_ref,
                },
            )
            started = time.perf_counter()
            status = "passed"
            failure_ref: str | None = None
            try:
                if (
                    product_snapshot is not None
                    and spec.function_name in DIRECT_PRODUCT_VALIDATORS
                ):
                    product_snapshot.run(spec.function_name)
                else:
                    legacy.run_timed(
                        None,
                        f"static_scan:{spec.name}",
                        getattr(legacy, spec.function_name),
                    )
            except BaseException as exc:
                status = "failed"
                failure_ref = f"exception-ref:{type(exc).__name__}"
                print(f"STATIC_SCAN_FAILURE:{spec.scan_ref}:{failure_ref}")
            outcomes.append(
                {
                    "scan_index": spec.index,
                    "scan_ref": spec.scan_ref,
                    "name": spec.name,
                    "function_name": spec.function_name,
                    "status": status,
                    "elapsed_ms": round((time.perf_counter() - started) * 1000),
                    "failure_ref": failure_ref,
                }
            )
            _write_json(result_path, result_payload)
            if status != "passed":
                _write_json(
                    progress_path,
                    {
                        "schema_version": PROGRESS_SCHEMA,
                        "state": "failed",
                        "scan_index": spec.index,
                        "scan_ref": spec.scan_ref,
                    },
                )
                return 1

    if resolve_repository_sha(ROOT) != plan.repository_sha:
        raise ValueError("static scan worker repository identity changed")
    _write_json(
        progress_path,
        {
            "schema_version": PROGRESS_SCHEMA,
            "state": "completed",
            "scan_index": selected[-1].index,
            "scan_ref": selected[-1].scan_ref,
        },
    )
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one isolated static scan shard.")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--progress", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return run_worker(
            Path(args.plan),
            Path(args.result),
            Path(args.progress),
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"STATIC_SCAN_WORKER_CONFIGURATION_ERROR:{type(exc).__name__}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
