from __future__ import annotations

import json
from pathlib import Path

import scripts.verify_uaa_p1_064_local_model_inventory_scope as verifier


ROOT = Path(__file__).resolve().parents[1]


def test_uaa_p1_064_scope_verifier_passes_current_repo() -> None:
    assert verifier.validate_uaa_p1_064_local_model_inventory_scope() == []


def test_uaa_p1_064_scope_doc_pins_read_only_cli_non_goals() -> None:
    text = (
        ROOT / "docs/model_management/UAA_P1_064_LOCAL_MODEL_INVENTORY_READ_ONLY.md"
    ).read_text(encoding="utf-8")

    assert "Status: Implemented" in text
    assert "read-only Python Agent Core inventory" in text
    assert "src/ultimate_ai_agent/core/local_model_management/inventory.py" in text
    assert "scripts/dev/uaa_local_model.py" in text
    assert "uaa local-model status" in text
    assert "uaa local-model list" in text
    assert "uaa local-model inspect <model-ref>" in text
    assert "No start, stop, activate, switch, or unload behavior" in text
    assert "No process control and no llama.cpp lifecycle management" in text
    assert "No OpenAPI or route authority" in text
    assert "No model downloads or model movement" in text
    assert "Stop And Ask Conditions" in text


def test_uaa_p1_064_reconciliation_artifact_points_to_restart_prompt() -> None:
    artifact = json.loads(
        (
            ROOT
            / "docs/backlog/reconciliation/2026-06-21-uaa-p1-064-ready-next-promotion.json"
        ).read_text(encoding="utf-8")
    )

    assert artifact["next_prompt_ref"] == (
        "prompt-ref:uaa-p1-065-founder-command-center-review-cleanup"
    )
    assert set(artifact["reconciliation_safety"]) == verifier.REQUIRED_SAFETY_FLAGS
    assert all(value is False for value in artifact["reconciliation_safety"].values())
    assert artifact["completed_recommendations"][0]["recommendation_ref"] == (
        "recommendation:uaa-p1-064-ready-next-scope"
    )
    assert artifact["completed_recommendations"][1]["recommendation_ref"] == (
        "recommendation:uaa-p1-064-implementation"
    )
    assert artifact["deferred_recommendations"][0]["reason_code"] == (
        "OUTSIDE_CURRENT_MILESTONE"
    )
    assert artifact["blocked_recommendations"][0]["reason_code"] == (
        "MISSING_SCOPED_AUTHORITY"
    )


def test_uaa_p1_064_scope_verifier_reports_missing_board_promotion(
    tmp_path: Path,
) -> None:
    source_files = [
        "docs/model_management/UAA_P1_064_LOCAL_MODEL_INVENTORY_READ_ONLY.md",
        "docs/kanban/current_board.md",
        "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md",
        "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
        "docs/control_center/OPERATOR_SHELL_GAP_MAP.md",
        "docs/README.md",
        "docs/DOCUMENTATION_INDEX.md",
        "docs/canonical/CANONICAL_DOC_MAP.md",
        "docs/backlog/codex_recommendation_log.md",
        "docs/backlog/reconciliation/2026-06-21-uaa-p1-064-ready-next-promotion.json",
    ]
    for rel_path in source_files:
        src = ROOT / rel_path
        dst = tmp_path / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    board_path = tmp_path / "docs/kanban/current_board.md"
    board_text = board_path.read_text(encoding="utf-8")
    board_path.write_text(
        board_text.replace(
            "UAA-P1-064 Local Model Inventory Read-Only Backend + CLI",
            "A future milestone is ready.",
        ),
        encoding="utf-8",
    )

    failures = verifier.validate_uaa_p1_064_local_model_inventory_scope(tmp_path)

    assert any(
        "UAA-P1-064 Local Model Inventory Read-Only Backend + CLI" in failure
        for failure in failures
    )


def test_uaa_p1_064_scope_script_does_not_execute_commands() -> None:
    script = verifier.__file__
    assert script is not None
    text = Path(script).read_text(encoding="utf-8")

    assert "import subprocess" not in text
    assert "os.system" not in text
    assert "subprocess.run" not in text
