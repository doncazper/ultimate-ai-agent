from pathlib import Path

from ultimate_ai_agent.core.production_readiness import REQUIRED_M167_HARDWARE_PROFILES


MATRIX_PATH = Path("docs/production/M167_LIVE_MODEL_EVIDENCE_MATRIX.md")


def _matrix_rows() -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for line in MATRIX_PATH.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if cells and cells[0] in {
            "Apple Silicon",
            "CPU-only",
            "Low RAM",
            "Discrete GPU",
            "Limited disk",
        }:
            rows[cells[0]] = cells
    return rows


def test_m167_live_model_matrix_has_required_safe_ref_rows():
    rows = _matrix_rows()

    assert list(rows) == [
        "Apple Silicon",
        "CPU-only",
        "Low RAM",
        "Discrete GPU",
        "Limited disk",
    ]
    assert [
        row[1].removeprefix("evidence-ref:m167:matrix:").replace("-", "_")
        for row in rows.values()
    ] == list(REQUIRED_M167_HARDWARE_PROFILES)

    for profile, row in rows.items():
        assert len(row) == 10
        assert row[1].startswith("evidence-ref:m167:matrix:")
        assert row[2].startswith("review-ref:m167:")
        assert row[4] == "model-ref:m167:approved-gguf:pending"
        assert "llama.cpp" not in row[5].lower() or "pending" in row[5].lower()
        assert "blocker-ref:m167:" in row[6]
        assert row[7].startswith("verification-ref:m167:")
        assert "rollback-ref:m167:known-good-local-model:pending" in row[8]
        assert any(status in row[9].lower() for status in {"pending", "blocked"})
        assert "proven" not in row[9].lower()
        assert "not production-ready" in row[9].lower() or row[9].lower().startswith("blocked;")
        assert profile


def test_m167_live_model_matrix_documents_status_semantics_and_scope_denials():
    text = MATRIX_PATH.read_text(encoding="utf-8").lower()

    for fragment in [
        "proven: reviewed live evidence exists",
        "pending: the row is scoped",
        "blocked: the row is scoped",
        "not-scoped: the behavior is outside this task",
        "no hardware row is proven in this patch",
        "m166 remains the authority gate",
        "does not start llama.cpp",
        "does not scope remote model servers",
        "tool/function calling",
        "m166 authority-gate binding",
    ]:
        assert fragment in text
