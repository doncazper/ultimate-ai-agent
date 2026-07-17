#!/usr/bin/env python3
"""Verify MSG-MX-009 exact room, encrypted-search, and media truth."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.authority.authority_constants import (
    MATRIX_ROOMS_MEDIA_COMPOSITE_REQUESTED_DOMAINS,
    MATRIX_ROOMS_MEDIA_EXACT_AUTHORITY_BINDINGS,
)
from ultimate_ai_agent.core.communications.matrix_rooms_media import (
    MATRIX_ROOMS_MEDIA_LANES,
    MatrixRoomsMediaOperation,
    build_default_matrix_rooms_media_posture,
)
from ultimate_ai_agent.core.communications.matrix_rooms_media.constants import (
    MATRIX_MEDIA_CANCEL_POLICY_REF,
    MATRIX_MEDIA_PREVIEW_POLICY_REF,
    MATRIX_MEDIA_PROGRESS_POLICY_REF,
    MATRIX_MEDIA_QUARANTINE_POLICY_REF,
    MATRIX_MEDIA_RETRY_POLICY_REF,
    MATRIX_SEARCH_INDEX_POLICY_REF,
)


ROOT = Path(__file__).resolve().parents[1]
BROKER_ROOT = ROOT / "integrations/matrix-rust-broker"
OPERATION_PREFIX = "/control-center/communications/matrix-rooms-media/"
POSTURE_ROUTE = OPERATION_PREFIX + "posture"
PROPOSAL_ROUTE = OPERATION_PREFIX + "proposal"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_broker_integrity(failures: list[str]) -> None:
    path = BROKER_ROOT / "runtime-integrity.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        failures.append("Matrix Rust broker integrity metadata is unavailable")
        return
    if (
        manifest.get("schema_version") != "uaa-matrix-rust-broker-integrity.v1"
        or manifest.get("rust_toolchain") != "1.93.0"
        or manifest.get("remote_targets_enabled") is not False
        or manifest.get("loopback_only") is not True
        or manifest.get("cargo_lock_sha256") != _sha256(BROKER_ROOT / "Cargo.lock")
        or manifest.get("cargo_manifest_sha256") != _sha256(BROKER_ROOT / "Cargo.toml")
    ):
        failures.append("Matrix Rust broker integrity posture drifted")
    expected_sources = {
        source.name: _sha256(source)
        for source in sorted((BROKER_ROOT / "src").glob("*.rs"))
    }
    if manifest.get("source_sha256") != expected_sources:
        failures.append("Matrix Rust broker reviewed source digests drifted")


def verify(root: Path = ROOT) -> list[str]:
    if root != ROOT:
        return ["MSG-MX-009 verifier supports the current repository root only"]
    failures: list[str] = []
    if set(MATRIX_ROOMS_MEDIA_LANES) != set(MatrixRoomsMediaOperation):
        failures.append("Matrix rooms/media operation-to-lane set is not closed")
    if len(MATRIX_ROOMS_MEDIA_LANES) != 20:
        failures.append("twenty exact Matrix rooms/media lanes are required")
    expected_bindings = {
        (
            lane.authority_domain.value,
            lane.authority_capability.value,
            "session",
            lane.required_mode.value,
            lane.lane_ref,
            lane.capability_ref,
            lane.adapter_ref,
            lane.tool_ref,
        )
        for lane in MATRIX_ROOMS_MEDIA_LANES.values()
    }
    if set(MATRIX_ROOMS_MEDIA_EXACT_AUTHORITY_BINDINGS) != expected_bindings:
        failures.append("generic AuthorityLease rooms/media allowlist drifted")
    if MATRIX_ROOMS_MEDIA_COMPOSITE_REQUESTED_DOMAINS != {
        "media_upload": {"messages": ("upload",), "files": ("read",)},
        "media_download_quarantine": {
            "messages": ("download",),
            "files": ("write",),
        },
    }:
        failures.append("composite media authority map drifted")

    posture = build_default_matrix_rooms_media_posture()
    if (
        posture.runtime_status != "configuration_required"
        or len(posture.authority_lane_refs) != 20
        or len(posture.implemented_core_operation_refs) != 20
        or len(posture.blocked_live_operation_refs) != 20
        or posture.media_max_bytes != 24_576
        or posture.quarantine_policy_ref != MATRIX_MEDIA_QUARANTINE_POLICY_REF
        or posture.preview_policy_ref != MATRIX_MEDIA_PREVIEW_POLICY_REF
        or posture.progress_policy_ref != MATRIX_MEDIA_PROGRESS_POLICY_REF
        or posture.cancel_policy_ref != MATRIX_MEDIA_CANCEL_POLICY_REF
        or posture.retry_policy_ref != MATRIX_MEDIA_RETRY_POLICY_REF
        or posture.search_index_policy_ref != MATRIX_SEARCH_INDEX_POLICY_REF
        or posture.standing_authority_granted
        or posture.multi_account_enabled
        or posture.raw_content_included
        or posture.element_interoperability_status != "external_facility_required"
        or not posture.request_scoped_evaluation_required
    ):
        failures.append("default Matrix rooms/media posture no longer fails closed")

    routes = {
        route.path: route
        for route in build_api_manifest(app).routes
        if route.path.startswith(OPERATION_PREFIX)
    }
    if len(routes) != 22:
        failures.append("twenty-two Matrix rooms/media API routes are required")
    posture_route = routes.get(POSTURE_ROUTE)
    proposal_route = routes.get(PROPOSAL_ROUTE)
    if posture_route is None or (
        posture_route.side_effect_class != "none"
        or posture_route.route_classification != "local_sensitive"
        or not posture_route.protected_route
    ):
        failures.append("Matrix rooms/media posture route contract drifted")
    if proposal_route is None or (
        proposal_route.side_effect_class != "validation_only"
        or proposal_route.route_classification != "local_sensitive"
        or not proposal_route.protected_route
    ):
        failures.append("Matrix rooms/media proposal route contract drifted")
    for operation, lane in MATRIX_ROOMS_MEDIA_LANES.items():
        path = OPERATION_PREFIX + operation.value.replace("_", "-")
        route = routes.get(path)
        if route is None or (
            route.side_effect_class != lane.side_effect_class
            or route.route_classification != "mutating_requires_authority"
            or not route.idempotency_required
            or not route.protected_route
            or route.rate_limit_group != "communications_matrix_rooms_media"
        ):
            failures.append(f"exact Matrix rooms/media route drifted: {path}")

    _verify_broker_integrity(failures)
    doc = ROOT / "docs/connectors/MESSENGER_MATRIX_ROOMS_SEARCH_MEDIA.md"
    try:
        doc_text = doc.read_text(encoding="utf-8")
    except OSError:
        failures.append("MSG-MX-009 canonical documentation is unavailable")
        doc_text = ""
    for marker in (
        "twenty separately evaluated operations",
        "parser-ref:matrix-media:metadata-only-v1",
        "manual, same-idempotency only",
        "all sixteen native network lanes",
        "external_facility_required",
        "zero containers, networks, volumes, and residual resources",
    ):
        if marker not in doc_text:
            failures.append(f"MSG-MX-009 documentation marker missing: {marker}")
    for relative in (
        "src/ultimate_ai_agent/core/communications/matrix_rooms_media/contracts.py",
        "src/ultimate_ai_agent/core/communications/matrix_rooms_media/search.py",
        "src/ultimate_ai_agent/core/communications/matrix_rooms_media/media.py",
        "src/ultimate_ai_agent/core/communications/matrix_rooms_media/service.py",
        "tests/test_msg_mx_009_rooms_search_media_contracts.py",
        "tests/test_msg_mx_009_rooms_search_media_api_cli.py",
    ):
        if not (ROOT / relative).is_file():
            failures.append(f"missing MSG-MX-009 artifact: {relative}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("MSG-MX-009 rooms/search/media verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("MSG-MX-009 rooms/search/media verification PASSED")
    print(
        json.dumps(
            {
                "accepted_exact_authority_lanes": 20,
                "implemented_core_operations": 20,
                "default_blocked_live_operations": 20,
                "media_max_bytes": 24_576,
                "runtime": "configuration_required",
                "multi_account": False,
                "element_interoperability": "external_facility_required",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
