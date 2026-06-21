from __future__ import annotations

import json
from pathlib import Path

import scripts.verify_morning_reconciliation_artifact as verifier


ROOT = Path(__file__).resolve().parents[1]


def test_morning_reconciliation_verifier_passes_current_repo() -> None:
    assert verifier.validate_morning_reconciliation_artifact() == []


def test_morning_reconciliation_schema_and_template_cover_required_buckets() -> None:
    schema = json.loads(
        (ROOT / "docs/schemas/morning_reconciliation_artifact.schema.json").read_text(
            encoding="utf-8"
        )
    )
    template = json.loads(
        (ROOT / "docs/backlog/MORNING_RECONCILIATION_TEMPLATE.json").read_text(
            encoding="utf-8"
        )
    )

    assert schema["properties"]["schema_version"]["const"] == verifier.SCHEMA_VERSION
    assert schema["properties"]["task_ref"]["const"] == verifier.TASK_REF
    assert schema["properties"]["operator_readiness_taxonomy_ref"]["const"] == (
        verifier.TAXONOMY_REF
    )
    assert schema["properties"]["recommendation_log_ref"]["const"] == (
        verifier.RECOMMENDATION_LOG_REF
    )
    assert set(schema["required"]) == verifier.REQUIRED_TOP_LEVEL_KEYS
    assert set(template) == verifier.REQUIRED_TOP_LEVEL_KEYS

    for bucket, status in verifier.BUCKETS.items():
        assert bucket in schema["properties"]
        assert template[bucket][0]["status"] == status


def test_morning_reconciliation_safety_flags_are_false() -> None:
    template = json.loads(
        (ROOT / "docs/backlog/MORNING_RECONCILIATION_TEMPLATE.json").read_text(
            encoding="utf-8"
        )
    )

    assert set(template["reconciliation_safety"]) == verifier.REQUIRED_SAFETY_FLAGS
    assert all(value is False for value in template["reconciliation_safety"].values())


def test_morning_reconciliation_artifact_instances_are_checked() -> None:
    artifacts = sorted(
        (ROOT / "docs/backlog/reconciliation").glob("*.json")
    )

    assert artifacts
    for artifact_path in artifacts:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))

        assert artifact["schema_version"] == verifier.SCHEMA_VERSION
        assert artifact["task_ref"] == verifier.TASK_REF
        assert artifact["reconciliation_id"] != "reconciliation:example-morning-loop"
        assert artifact["source_loop_ref"] != "loop:example-codex-conveyor"
        assert set(artifact["reconciliation_safety"]) == verifier.REQUIRED_SAFETY_FLAGS
        assert all(value is False for value in artifact["reconciliation_safety"].values())
        for bucket, status in verifier.BUCKETS.items():
            assert artifact[bucket][0]["status"] == status


def test_morning_reconciliation_verifier_reports_missing_bucket(tmp_path: Path) -> None:
    source_files = [
        "docs/backlog/MORNING_RECONCILIATION_ARTIFACT.md",
        "docs/backlog/MORNING_RECONCILIATION_TEMPLATE.json",
        "docs/schemas/morning_reconciliation_artifact.schema.json",
        "docs/backlog/reconciliation/README.md",
        "docs/backlog/reconciliation/2026-06-21-conveyor-reconciliation-durability.json",
        "docs/backlog/codex_recommendation_log.md",
        "docs/kanban/current_board.md",
        "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md",
    ]
    for rel_path in source_files:
        src = ROOT / rel_path
        dst = tmp_path / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    template_path = tmp_path / "docs/backlog/MORNING_RECONCILIATION_TEMPLATE.json"
    template = json.loads(template_path.read_text(encoding="utf-8"))
    template["blocked_recommendations"] = []
    template_path.write_text(json.dumps(template), encoding="utf-8")

    failures = verifier.validate_morning_reconciliation_artifact(tmp_path)

    assert (
        "morning reconciliation template missing bucket: blocked_recommendations"
        in failures
    )


def test_morning_reconciliation_verifier_reports_example_instance(tmp_path: Path) -> None:
    source_files = [
        "docs/backlog/MORNING_RECONCILIATION_ARTIFACT.md",
        "docs/backlog/MORNING_RECONCILIATION_TEMPLATE.json",
        "docs/schemas/morning_reconciliation_artifact.schema.json",
        "docs/backlog/reconciliation/README.md",
        "docs/backlog/reconciliation/2026-06-21-conveyor-reconciliation-durability.json",
        "docs/backlog/codex_recommendation_log.md",
        "docs/kanban/current_board.md",
        "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md",
    ]
    for rel_path in source_files:
        src = ROOT / rel_path
        dst = tmp_path / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    artifact_path = (
        tmp_path
        / "docs/backlog/reconciliation/2026-06-21-conveyor-reconciliation-durability.json"
    )
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    artifact["reconciliation_id"] = "reconciliation:example-morning-loop"
    artifact["source_loop_ref"] = "loop:example-codex-conveyor"
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

    failures = verifier.validate_morning_reconciliation_artifact(tmp_path)

    assert any("must replace the example reconciliation_id" in failure for failure in failures)
    assert any("must replace the example source_loop_ref" in failure for failure in failures)


def test_morning_reconciliation_script_does_not_execute_commands() -> None:
    script = verifier.__file__
    assert script is not None
    text = Path(script).read_text(encoding="utf-8")

    assert "import subprocess" not in text
    assert "os.system" not in text
    assert "subprocess.run" not in text
