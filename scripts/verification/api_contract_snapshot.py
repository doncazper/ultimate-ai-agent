#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from scripts.verification.api_route_policy_floor import (
        validate_route_policy_floor,
    )
except ModuleNotFoundError:  # Direct script execution from the repository root.
    from api_route_policy_floor import validate_route_policy_floor


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = ROOT / "tests/fixtures/api_route_inventory_133.json"
SNAPSHOT_SCHEMA_VERSION = "uaa-api-route-inventory.v5"
DOC_COUNT_PATHS = (
    ROOT / "docs/api/README.md",
    ROOT / "docs/api/openapi_contract.md",
    ROOT / "docs/api/route_inventory.md",
)
DOC_COUNT_START = "<!-- uaa-api-contract-counts:start -->"
DOC_COUNT_END = "<!-- uaa-api-contract-counts:end -->"
ROUTE_PROJECTION_FIELDS = (
    "path",
    "method",
    "operation_id",
    "tags",
    "summary",
    "side_effect_class",
    "route_classification",
    "auth_posture",
    "approval_posture",
    "idempotency_required",
    "idempotency_posture",
    "idempotency_policy_ref",
    "rate_limit_targeted",
    "rate_limit_posture",
    "rate_limit_policy_ref",
    "rate_limit_group",
)


def _canonical(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _fingerprint(payload: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "fingerprint"}
    return f"api-contract-fingerprint:sha256:{hashlib.sha256(_canonical(unsigned)).hexdigest()}"


def _project_routes(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    routes = [
        {field: route[field] for field in ROUTE_PROJECTION_FIELDS}
        for route in manifest["routes"]
    ]
    return sorted(routes, key=lambda item: (item["path"], item["method"]))


def _operations_from_openapi(
    openapi: dict[str, Any],
) -> dict[tuple[str, str], str | None]:
    return {
        (method.upper(), path): operation.get("operationId")
        for path, methods in openapi.get("paths", {}).items()
        for method, operation in methods.items()
        if method.lower()
        in {"get", "post", "put", "patch", "delete", "options", "head"}
    }


def _route_summary(routes: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(route[field] for route in routes).items()))


def build_snapshot() -> dict[str, Any]:
    from ultimate_ai_agent.api.app import app
    from ultimate_ai_agent.api.manifest import build_api_manifest

    manifest = build_api_manifest(app).model_dump(mode="json")
    openapi = app.openapi()
    return build_snapshot_from_sources(manifest, openapi)


def build_snapshot_from_sources(
    manifest: dict[str, Any], openapi: dict[str, Any]
) -> dict[str, Any]:
    routes = _project_routes(manifest)
    validate_route_policy_floor(routes)
    route_keys = [(route["method"], route["path"]) for route in routes]
    operation_ids = [route["operation_id"] for route in routes]
    manifest_operations = {
        (route["method"], route["path"]): route["operation_id"] for route in routes
    }
    openapi_operations = _operations_from_openapi(openapi)
    if len(route_keys) != len(set(route_keys)):
        raise ValueError("API_CONTRACT_DUPLICATE_ROUTE_KEY")
    if not all(operation_ids) or len(operation_ids) != len(set(operation_ids)):
        raise ValueError("API_CONTRACT_OPERATION_ID_INVALID")
    if manifest_operations != openapi_operations:
        raise ValueError("API_CONTRACT_OPENAPI_ROUTE_IDENTITY_DRIFT")

    summary_fields = {
        "route_classification_summary": "route_classification",
        "route_auth_posture_summary": "auth_posture",
        "route_approval_posture_summary": "approval_posture",
        "route_idempotency_posture_summary": "idempotency_posture",
        "route_rate_limit_posture_summary": "rate_limit_posture",
    }
    summaries = {
        summary_key: _route_summary(routes, field)
        for summary_key, field in summary_fields.items()
    }
    for summary_key, summary in summaries.items():
        if manifest.get(summary_key) != summary:
            raise ValueError(f"API_CONTRACT_MANIFEST_SUMMARY_DRIFT:{summary_key}")
    payload: dict[str, Any] = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "schema_ref": "schema-ref:api-contract-snapshot:v1",
        "source_ref": "source-ref:fastapi-openapi-and-api-manifest",
        "route_operation_count": len(routes),
        "route_count": len(routes),
        "openapi_path_count": len(openapi.get("paths", {})),
        "control_center_route_count": sum(
            route["path"].startswith("/control-center/") for route in routes
        ),
        "mutating_route_count": sum(
            route["route_classification"] == "mutating_requires_authority"
            for route in routes
        ),
        "targeted_rate_limit_route_count": sum(
            bool(route["rate_limit_targeted"]) for route in routes
        ),
        "projection_fields": list(ROUTE_PROJECTION_FIELDS),
        "route_classification_vocabulary": manifest["route_classification_vocabulary"],
        "route_classification_summary": summaries["route_classification_summary"],
        "route_auth_posture_summary": summaries["route_auth_posture_summary"],
        "route_approval_posture_summary": summaries["route_approval_posture_summary"],
        "route_idempotency_posture_summary": summaries[
            "route_idempotency_posture_summary"
        ],
        "idempotency_audit_policy_ref": manifest["idempotency_audit_policy_ref"],
        "route_rate_limit_posture_summary": summaries[
            "route_rate_limit_posture_summary"
        ],
        "rate_limit_policy_ref": manifest["rate_limit_policy_ref"],
        "routes": routes,
        "static_declaration_only": True,
        "runtime_authority_included": False,
    }
    for summary_key in (
        "route_classification_summary",
        "route_auth_posture_summary",
        "route_approval_posture_summary",
        "route_idempotency_posture_summary",
        "route_rate_limit_posture_summary",
    ):
        if sum(payload[summary_key].values()) != len(routes):
            raise ValueError(f"API_CONTRACT_SUMMARY_TOTAL_INVALID:{summary_key}")
    payload["fingerprint"] = _fingerprint(payload)
    return payload


def load_snapshot(path: Path = SNAPSHOT_PATH) -> dict[str, Any]:
    payload = json.loads(_read_regular_text(path))
    if payload.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        raise ValueError("API_CONTRACT_SNAPSHOT_SCHEMA_INVALID")
    if payload.get("fingerprint") != _fingerprint(payload):
        raise ValueError("API_CONTRACT_SNAPSHOT_FINGERPRINT_INVALID")
    return payload


def check_snapshot(path: Path = SNAPSHOT_PATH) -> tuple[bool, dict[str, Any]]:
    current = build_snapshot()
    try:
        stored = load_snapshot(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return False, current
    documentation_current = True
    if path == SNAPSHOT_PATH:
        expected_block = _documentation_count_block(current)
        documentation_current = all(
            expected_block in _read_regular_text(doc_path)
            for doc_path in DOC_COUNT_PATHS
        )
    return stored == current and documentation_current, current


def _documentation_count_block(payload: dict[str, Any]) -> str:
    return (
        f"{DOC_COUNT_START}\n"
        f"Current generated contract snapshot: "
        f"`{payload['openapi_path_count']}` OpenAPI paths and "
        f"`{payload['route_operation_count']}` manifest route operations.\n"
        f"{DOC_COUNT_END}"
    )


def _read_regular_text(path: Path) -> str:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("API_CONTRACT_ARTIFACT_NOT_REGULAR")
        with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
            descriptor = -1
            return handle.read()
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _stage_text(path: Path, content: str) -> Path:
    parent = path.parent
    parent_metadata = parent.lstat()
    if parent.is_symlink() or not stat.S_ISDIR(parent_metadata.st_mode):
        raise ValueError("API_CONTRACT_ARTIFACT_PARENT_INVALID")
    mode = 0o644
    if path.exists():
        metadata = path.lstat()
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            raise ValueError("API_CONTRACT_ARTIFACT_TARGET_INVALID")
        mode = stat.S_IMODE(metadata.st_mode)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temp, flags, mode)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        return temp
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temp.exists() and temp.stat().st_size != len(content.encode("utf-8")):
            temp.unlink()


def refresh_snapshot(
    payload: dict[str, Any],
    *,
    snapshot_path: Path = SNAPSHOT_PATH,
    doc_paths: tuple[Path, ...] = DOC_COUNT_PATHS,
) -> None:
    if snapshot_path.exists():
        _read_regular_text(snapshot_path)
    replacement = _documentation_count_block(payload)
    outputs: dict[Path, str] = {
        snapshot_path: json.dumps(payload, indent=2, sort_keys=True) + "\n"
    }
    for path in doc_paths:
        source = _read_regular_text(path)
        if source.count(DOC_COUNT_START) != 1 or source.count(DOC_COUNT_END) != 1:
            raise ValueError("API_CONTRACT_DOCUMENTATION_MARKER_INVALID")
        start = source.index(DOC_COUNT_START)
        end = source.index(DOC_COUNT_END, start) + len(DOC_COUNT_END)
        outputs[path] = source[:start] + replacement + source[end:]
    staged: dict[Path, Path] = {}
    try:
        for path, content in outputs.items():
            staged[path] = _stage_text(path, content)
        for path, temp in staged.items():
            os.replace(temp, path)
        for parent in {path.parent for path in outputs}:
            directory = os.open(parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        for temp in staged.values():
            if temp.exists():
                temp.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check or refresh the canonical static API contract snapshot."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--refresh", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    current = build_snapshot()
    if args.refresh:
        refresh_snapshot(current)
        status = "refreshed"
        success = True
    else:
        success, _ = check_snapshot(SNAPSHOT_PATH)
        status = "current" if success else "stale"
    output = {
        "schema_version": "uaa-api-contract-snapshot-check.v1",
        "status": status,
        "fingerprint": current["fingerprint"],
        "route_operation_count": current["route_operation_count"],
        "openapi_path_count": current["openapi_path_count"],
        "static_declaration_only": True,
        "release_gate_equivalent": False,
    }
    if args.json:
        print(json.dumps(output, sort_keys=True))
    else:
        print(
            "API contract snapshot: "
            f"{status}; routes={output['route_operation_count']} "
            f"paths={output['openapi_path_count']}"
        )
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
