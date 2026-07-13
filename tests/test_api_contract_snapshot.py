from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.verification import api_contract_snapshot as snapshot


def _sources_from_snapshot() -> tuple[dict[str, object], dict[str, object]]:
    stored = snapshot.load_snapshot()
    manifest = {
        key: stored[key]
        for key in (
            "route_classification_vocabulary",
            "route_classification_summary",
            "route_auth_posture_summary",
            "route_approval_posture_summary",
            "route_idempotency_posture_summary",
            "idempotency_audit_policy_ref",
            "route_rate_limit_posture_summary",
            "rate_limit_policy_ref",
            "routes",
        )
    }
    paths: dict[str, dict[str, dict[str, str]]] = {}
    for route in stored["routes"]:
        paths.setdefault(route["path"], {})[route["method"].lower()] = {
            "operationId": route["operation_id"]
        }
    return manifest, {"paths": paths}


def test_canonical_api_snapshot_is_current_and_deterministic() -> None:
    first = snapshot.build_snapshot()
    second = snapshot.build_snapshot()

    assert first == second == snapshot.load_snapshot()
    assert snapshot.check_snapshot()[0] is True
    assert first["route_operation_count"] == len(first["routes"])
    assert first["fingerprint"].startswith("api-contract-fingerprint:sha256:")


def test_snapshot_check_detects_stale_or_tampered_artifact(tmp_path: Path) -> None:
    stale = snapshot.load_snapshot().copy()
    stale["route_operation_count"] += 1
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(stale), encoding="utf-8")

    assert snapshot.check_snapshot(path)[0] is False


def test_snapshot_builder_rejects_duplicate_route_or_operation_id() -> None:
    manifest, openapi = _sources_from_snapshot()
    duplicate_route = dict(manifest)
    duplicate_route["routes"] = [*manifest["routes"], manifest["routes"][0]]
    with pytest.raises(ValueError, match="DUPLICATE_ROUTE_KEY"):
        snapshot.build_snapshot_from_sources(duplicate_route, openapi)

    duplicate_operation = dict(manifest)
    routes = [dict(route) for route in manifest["routes"]]
    routes[1]["operation_id"] = routes[0]["operation_id"]
    duplicate_operation["routes"] = routes
    with pytest.raises(ValueError, match="OPERATION_ID_INVALID"):
        snapshot.build_snapshot_from_sources(duplicate_operation, openapi)


def test_snapshot_builder_rejects_openapi_route_identity_drift() -> None:
    manifest, openapi = _sources_from_snapshot()
    health = openapi["paths"].pop("/health")
    openapi["paths"]["/health-renamed"] = health

    with pytest.raises(ValueError, match="OPENAPI_ROUTE_IDENTITY_DRIFT"):
        snapshot.build_snapshot_from_sources(manifest, openapi)


def test_snapshot_builder_rejects_stale_manifest_summary_with_same_total() -> None:
    manifest, openapi = _sources_from_snapshot()
    summary = dict(manifest["route_rate_limit_posture_summary"])
    keys = sorted(summary)
    summary[keys[0]] += 1
    summary[keys[1]] -= 1
    manifest["route_rate_limit_posture_summary"] = summary

    with pytest.raises(ValueError, match="MANIFEST_SUMMARY_DRIFT"):
        snapshot.build_snapshot_from_sources(manifest, openapi)


@pytest.mark.parametrize(
    ("route_key", "field", "value", "error"),
    [
        (
            ("GET", "/health"),
            "route_classification",
            "local_readonly",
            "PUBLIC_ROUTE_POLICY_DRIFT",
        ),
        (
            ("POST", "/api/runtime/safe-disable"),
            "approval_posture",
            "not_required_for_route_classification",
            "MUTATION_GUARD_POLICY_DRIFT",
        ),
        (
            ("POST", "/api/runtime/safe-disable"),
            "rate_limit_targeted",
            False,
            "RATE_LIMIT_COUNT_POLICY_DRIFT",
        ),
        (
            ("GET", "/health"),
            "approval_posture",
            "required_before_mutation_authority",
            "NONMUTATING_GUARD_POLICY_DRIFT",
        ),
        (
            ("GET", "/health"),
            "idempotency_required",
            True,
            "NONMUTATING_GUARD_POLICY_DRIFT",
        ),
        (
            ("GET", "/health"),
            "idempotency_posture",
            "required_before_mutation_authority",
            "NONMUTATING_GUARD_POLICY_DRIFT",
        ),
    ],
)
def test_snapshot_refresh_cannot_redefine_security_policy_floor(
    route_key: tuple[str, str],
    field: str,
    value: object,
    error: str,
) -> None:
    manifest, openapi = _sources_from_snapshot()
    routes = [dict(route) for route in manifest["routes"]]
    route = next(
        route for route in routes if (route["method"], route["path"]) == route_key
    )
    route[field] = value
    manifest["routes"] = routes

    with pytest.raises(ValueError, match=error):
        snapshot.build_snapshot_from_sources(manifest, openapi)


def test_snapshot_policy_floor_pins_exact_targeted_rate_limit_routes() -> None:
    manifest, openapi = _sources_from_snapshot()
    routes = [dict(route) for route in manifest["routes"]]
    removed = next(route for route in routes if route["rate_limit_targeted"] is True)
    replacement = next(
        route for route in routes if route["rate_limit_targeted"] is False
    )
    rate_fields = (
        "rate_limit_targeted",
        "rate_limit_posture",
        "rate_limit_policy_ref",
        "rate_limit_group",
    )
    removed_values = {field: removed[field] for field in rate_fields}
    replacement_values = {field: replacement[field] for field in rate_fields}
    removed.update(replacement_values)
    replacement.update(removed_values)
    manifest["routes"] = routes
    manifest["route_rate_limit_posture_summary"] = dict(
        snapshot._route_summary(routes, "rate_limit_posture")
    )

    with pytest.raises(ValueError, match="RATE_LIMIT_ROUTE_POLICY_DRIFT"):
        snapshot.build_snapshot_from_sources(manifest, openapi)


def _doc(text: str = "old") -> str:
    return (
        f"before\n{snapshot.DOC_COUNT_START}\n{text}\n{snapshot.DOC_COUNT_END}\nafter\n"
    )


def test_refresh_preflights_every_marker_before_mutating_any_target(
    tmp_path: Path,
) -> None:
    snapshot_path = tmp_path / "snapshot.json"
    first = tmp_path / "first.md"
    missing = tmp_path / "missing.md"
    snapshot_path.write_text("old snapshot\n", encoding="utf-8")
    first.write_text(_doc(), encoding="utf-8")
    missing.write_text("no marker\n", encoding="utf-8")
    originals = {
        path: path.read_text(encoding="utf-8")
        for path in (snapshot_path, first, missing)
    }

    with pytest.raises(ValueError, match="DOCUMENTATION_MARKER_INVALID"):
        snapshot.refresh_snapshot(
            snapshot.build_snapshot(),
            snapshot_path=snapshot_path,
            doc_paths=(first, missing),
        )

    assert {
        path: path.read_text(encoding="utf-8")
        for path in (snapshot_path, first, missing)
    } == originals
    assert not list(tmp_path.glob(".*.tmp"))


def test_refresh_rejects_documentation_symlink_without_mutation(
    tmp_path: Path,
) -> None:
    snapshot_path = tmp_path / "snapshot.json"
    regular = tmp_path / "regular.md"
    outside = tmp_path / "outside.md"
    linked = tmp_path / "linked.md"
    snapshot_path.write_text("old snapshot\n", encoding="utf-8")
    regular.write_text(_doc(), encoding="utf-8")
    outside.write_text(_doc("outside"), encoding="utf-8")
    linked.symlink_to(outside)

    with pytest.raises(OSError):
        snapshot.refresh_snapshot(
            snapshot.build_snapshot(),
            snapshot_path=snapshot_path,
            doc_paths=(regular, linked),
        )

    assert snapshot_path.read_text(encoding="utf-8") == "old snapshot\n"
    assert regular.read_text(encoding="utf-8") == _doc()
    assert outside.read_text(encoding="utf-8") == _doc("outside")
