from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_msg_mx_003_communications_contracts.py"


def _load_verifier() -> Any:
    spec = importlib.util.spec_from_file_location(
        "verify_msg_mx_003_communications_contracts",
        SCRIPT,
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_msg_mx_003_verifier_passes_current_repository() -> None:
    verifier = _load_verifier()
    assert verifier.verify(ROOT) == []


def test_msg_mx_003_verifier_rejects_network_import(tmp_path: Path) -> None:
    verifier = _load_verifier()
    for relative in verifier.REQUIRED_PATHS:
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    for relative in (
        "src/ultimate_ai_agent/core/communications/__init__.py",
        "apps/control-center/src/api/endpoints.ts",
        "apps/control-center/src/api/client.ts",
        "apps/control-center/package.json",
        "apps/control-center/package-lock.json",
        "pyproject.toml",
        "docs/kanban/current_board.md",
        "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    adapter = tmp_path / "src/ultimate_ai_agent/core/communications/matrix_disabled.py"
    adapter.write_text(
        adapter.read_text(encoding="utf-8") + "\nimport requests\n",
        encoding="utf-8",
    )

    failures = verifier.verify(tmp_path)
    assert any("denied network or Matrix runtime" in failure for failure in failures)
