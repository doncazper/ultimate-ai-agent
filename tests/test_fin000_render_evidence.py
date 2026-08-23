from __future__ import annotations

import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDER_DIR = (
    ROOT
    / "docs"
    / "design"
    / "control_center_north_star"
    / "renders"
    / "finance-compliance-v1"
)

DESKTOP_RENDERS = (
    "01-finance-command-desktop.png",
    "02-source-statement-inbox-desktop.png",
    "03-extraction-reconciliation-workbench.png",
    "04-transfer-balance-sheet-review.png",
    "05-review-batches-desktop.png",
    "06-transaction-review-desktop.png",
    "07-transaction-evidence-inspector.png",
    "08-books-reconciliation-desktop.png",
    "09-tax-readiness-accountant-desktop.png",
    "10-compliance-obligations-desktop.png",
    "11-calendar-finance-saved-view.png",
    "12-founder-loop-finance-projections.png",
)

NARROW_RENDERS = (
    "13-finance-command-narrow.png",
    "14-transaction-review-narrow.png",
    "15-evidence-capture-narrow.png",
    "16-upcoming-obligations-narrow.png",
)


def _png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    assert header[:8] == b"\x89PNG\r\n\x1a\n"
    assert header[12:16] == b"IHDR"
    return struct.unpack(">II", header[16:24])


def test_fin000_render_candidate_inventory_is_complete_and_readable() -> None:
    actual = {path.name for path in RENDER_DIR.glob("*.png")}
    expected = {*DESKTOP_RENDERS, *NARROW_RENDERS}
    assert actual == expected

    for name in DESKTOP_RENDERS:
        width, height = _png_dimensions(RENDER_DIR / name)
        assert width >= 1440
        assert height >= 900

    for name in NARROW_RENDERS:
        width, height = _png_dimensions(RENDER_DIR / name)
        assert width >= 720
        assert height >= 1080


def test_fin000_docs_keep_render_acceptance_and_runtime_truth_explicit() -> None:
    brief = (RENDER_DIR / "README.md").read_text(encoding="utf-8")
    matrix = (
        ROOT / "docs" / "product" / "UAA_FINANCE_FIN000_ACCEPTANCE_MATRIX.md"
    ).read_text(encoding="utf-8")

    assert "independent review pending" in brief
    assert "does not sign the checklist" in brief
    assert "no Finance runtime is implemented" in matrix
    assert "independent acceptance pending" in matrix
