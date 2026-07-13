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
