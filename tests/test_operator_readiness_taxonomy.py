from __future__ import annotations

import json
from pathlib import Path

import scripts.verify_operator_readiness_taxonomy as verifier


ROOT = Path(__file__).resolve().parents[1]


def test_operator_readiness_taxonomy_verifier_passes() -> None:
    assert verifier.validate_operator_readiness_taxonomy() == []


def test_route_manifest_statuses_map_to_canonical_taxonomy() -> None:
    manifest = json.loads(
        (ROOT / "docs/control_center/route_status_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert manifest["operator_readiness_taxonomy_ref"] == verifier.TAXONOMY_REF
    assert manifest["release_status_taxonomy_map"] == verifier.ROUTE_STATUS_TAXONOMY_MAP
    assert set(manifest["allowed_release_statuses"]) == set(
        verifier.ROUTE_STATUS_TAXONOMY_MAP
    )


def test_release_packet_template_pins_taxonomy_ref() -> None:
    template = json.loads(
        (ROOT / "docs/production/RELEASE_EVIDENCE_PACKET_TEMPLATE.json").read_text(
            encoding="utf-8"
        )
    )

    assert template["operator_readiness_taxonomy_ref"] == verifier.TAXONOMY_REF
    assert set(template["status_semantics"]) == verifier.RELEASE_EVIDENCE_STATUSES


def test_taxonomy_verifier_reports_missing_route_manifest_mapping(tmp_path: Path) -> None:
    source_files = [
        "docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md",
        "docs/control_center/ROUTE_STATUS_MANIFEST.md",
        "docs/control_center/PRODUCT_LANGUAGE_RULES.md",
        "docs/production/RELEASE_VERIFICATION_LANES.md",
        "docs/production/RELEASE_EVIDENCE_PACKET.md",
        "docs/schemas/release_evidence_packet.schema.json",
        "docs/production/RELEASE_EVIDENCE_PACKET_TEMPLATE.json",
        "scripts/run_foundation_gate.py",
        "src/ultimate_ai_agent/core/gate/reports.py",
    ]
    for rel_path in source_files:
        src = ROOT / rel_path
        dst = tmp_path / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    bad_manifest = {
        "schema_version": "uaa-control-center-route-status.v1",
        "status": "active UAA-P1-030 route status manifest",
        "operator_readiness_taxonomy_ref": verifier.TAXONOMY_REF,
        "openapi_path_count": 125,
        "allowed_release_statuses": list(verifier.ROUTE_STATUS_TAXONOMY_MAP),
        "release_status_taxonomy_map": {},
        "surfaces": [],
        "visible_actions": [],
    }
    manifest_path = tmp_path / "docs/control_center/route_status_manifest.json"
    manifest_path.write_text(json.dumps(bad_manifest), encoding="utf-8")

    failures = verifier.validate_operator_readiness_taxonomy(tmp_path)

    assert "route status manifest release_status_taxonomy_map drifted" in failures
