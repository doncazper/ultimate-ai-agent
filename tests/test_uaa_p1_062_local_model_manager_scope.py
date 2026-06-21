from __future__ import annotations

import json
from pathlib import Path

import scripts.verify_uaa_p1_062_local_model_manager_scope as verifier


ROOT = Path(__file__).resolve().parents[1]


def test_uaa_p1_062_scope_verifier_passes_current_repo() -> None:
    assert verifier.validate_uaa_p1_062_local_model_manager_scope() == []


def test_uaa_p1_062_scope_doc_pins_docs_only_non_goals() -> None:
    text = (
        ROOT / "docs/model_management/UAA_P1_062_LOCAL_MODEL_MANAGER_SCOPE.md"
    ).read_text(encoding="utf-8")

    assert "Status: docs-only lane shape" in text
    assert "Python Agent Core owns local model truth" in text
    assert "no backend routes" in text
    assert "no CLI commands" in text
    assert "no process control" in text
    assert "no provider/model calls" in text
    assert "Future implementation stages need later documented scope" in text


def test_uaa_p1_062_reconciliation_artifact_blocks_runtime_authority() -> None:
    artifact = json.loads(
        (
            ROOT
            / "docs/backlog/reconciliation/2026-06-21-uaa-p1-062-local-model-manager-shape.json"
        ).read_text(encoding="utf-8")
    )

    assert artifact["next_prompt_ref"] == "prompt-ref:no-documented-ready-next"
    assert set(artifact["reconciliation_safety"]) == verifier.REQUIRED_SAFETY_FLAGS
    assert all(value is False for value in artifact["reconciliation_safety"].values())
    assert artifact["blocked_recommendations"][0]["reason_code"] == (
        "MISSING_SCOPED_AUTHORITY"
    )
    assert artifact["rejected_recommendations"][0]["reason_code"] == (
        "CONTROL_CENTER_NOT_AUTHORITY"
    )


def test_uaa_p1_062_scope_verifier_reports_missing_ready_next_stop(
    tmp_path: Path,
) -> None:
    source_files = [
        "docs/model_management/UAA_P1_062_LOCAL_MODEL_MANAGER_SCOPE.md",
        "docs/kanban/current_board.md",
        "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md",
        "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
        "docs/control_center/OPERATOR_SHELL_GAP_MAP.md",
        "docs/README.md",
        "docs/DOCUMENTATION_INDEX.md",
        "docs/canonical/CANONICAL_DOC_MAP.md",
        "docs/backlog/codex_recommendation_log.md",
        "docs/backlog/reconciliation/2026-06-21-uaa-p1-062-local-model-manager-shape.json",
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
            "No documented Ready Next milestone remains after UAA-P1-062.",
            "A future milestone is ready.",
        ),
        encoding="utf-8",
    )

    failures = verifier.validate_uaa_p1_062_local_model_manager_scope(tmp_path)

    assert any(
        "No documented Ready Next milestone remains after UAA-P1-062" in failure
        for failure in failures
    )


def test_uaa_p1_062_scope_script_does_not_execute_commands() -> None:
    script = verifier.__file__
    assert script is not None
    text = Path(script).read_text(encoding="utf-8")

    assert "import subprocess" not in text
    assert "os.system" not in text
    assert "subprocess.run" not in text
