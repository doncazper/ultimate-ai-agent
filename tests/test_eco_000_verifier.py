from __future__ import annotations

import json
from pathlib import Path

import scripts.verify_eco_000_ecosystem_contracts as verifier


ROOT = Path(__file__).resolve().parents[1]


def test_eco_000_verifier_passes() -> None:
    assert verifier.verify() == []


def test_eco_000_verifier_scans_nested_route_modules(tmp_path: Path) -> None:
    routes = tmp_path / "routes" / "nested"
    routes.mkdir(parents=True)
    (routes / "ecosystem.py").write_text(
        '@router.get("/ecosystem/status")\n',
        encoding="utf-8",
    )

    assert verifier._contains_runtime_ecosystem_route(tmp_path) is True


def test_render_manifest_is_traceable_and_non_shipping() -> None:
    payload = json.loads(
        (
            ROOT
            / "docs/design/ecosystem_north_star/render_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert payload["implementation_evidence"] is False
    assert payload["runtime_routes_added"] is False
    assert len(payload["surfaces"]) == 12
    assert all(item["status"] == "reviewed" for item in payload["surfaces"])
    assert all(item["shipped"] is False for item in payload["surfaces"])


def test_app_acceptance_is_complete_but_planning_only() -> None:
    payload = json.loads(
        (ROOT / "docs/product/eco_000_app_acceptance.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["implementation_authorized"] is False
    assert payload["runtime_routes_added"] is False
    assert {item["app_id"] for item in payload["apps"]} == verifier.REQUIRED_APPS
    assert all(item["status"] == "planned" for item in payload["apps"])


def test_verifier_rejects_duplicate_app_records(monkeypatch) -> None:
    original_load = verifier._load
    payload = original_load("docs/product/eco_000_app_acceptance.json")
    payload["apps"] = [*payload["apps"], payload["apps"][0]]
    monkeypatch.setattr(
        verifier,
        "_load",
        lambda relative: payload
        if relative == "docs/product/eco_000_app_acceptance.json"
        else original_load(relative),
    )

    assert "standalone app acceptance records must be unique" in verifier.verify()


def test_verifier_rejects_duplicate_surface_and_asset_records(monkeypatch) -> None:
    original_load = verifier._load
    payload = original_load("docs/design/ecosystem_north_star/render_manifest.json")
    payload["surfaces"] = [*payload["surfaces"], payload["surfaces"][0]]
    monkeypatch.setattr(
        verifier,
        "_load",
        lambda relative: payload
        if relative == "docs/design/ecosystem_north_star/render_manifest.json"
        else original_load(relative),
    )

    failures = verifier.verify()
    assert "render surface/state records must be unique" in failures
    assert "render assets must be unique per surface/state" in failures


def test_verifier_rejects_unknown_schema_and_milestone(monkeypatch) -> None:
    original_load = verifier._load
    acceptance = original_load("docs/product/eco_000_app_acceptance.json")
    acceptance["schema_version"] = "uaa-eco-000-app-acceptance.v999"
    acceptance["milestone_ref"] = "milestone-ref:ECO-OTHER"
    render_manifest = original_load(
        "docs/design/ecosystem_north_star/render_manifest.json"
    )
    render_manifest["schema_version"] = "uaa-eco-000-render-manifest.v999"
    render_manifest["milestone_ref"] = "milestone-ref:ECO-OTHER"
    replacements = {
        "docs/product/eco_000_app_acceptance.json": acceptance,
        "docs/design/ecosystem_north_star/render_manifest.json": render_manifest,
    }
    monkeypatch.setattr(
        verifier,
        "_load",
        lambda relative: replacements.get(relative, original_load(relative)),
    )

    failures = verifier.verify()
    assert "ECO-000 app acceptance schema version is unsupported" in failures
    assert "ECO-000 app acceptance milestone binding is invalid" in failures
    assert "ECO-000 render manifest schema version is unsupported" in failures
    assert "ECO-000 render manifest milestone binding is invalid" in failures


def test_verifier_rejects_render_asset_traversal(monkeypatch) -> None:
    original_load = verifier._load
    manifest = original_load("docs/design/ecosystem_north_star/render_manifest.json")
    manifest["surfaces"][0]["asset"] = "../outside.svg"
    monkeypatch.setattr(
        verifier,
        "_load",
        lambda relative: manifest
        if relative == "docs/design/ecosystem_north_star/render_manifest.json"
        else original_load(relative),
    )

    assert any(
        failure.startswith("render asset path is unsafe:")
        for failure in verifier.verify()
    )
