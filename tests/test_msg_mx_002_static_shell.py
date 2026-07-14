from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_msg_mx_002_static_shell.py"


def _load_verifier() -> Any:
    spec = importlib.util.spec_from_file_location("verify_msg_mx_002_static_shell", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_msg_mx_002_static_shell_verifier_passes_current_repo() -> None:
    verifier = _load_verifier()

    assert verifier.verify(ROOT) == []


def test_msg_mx_002_verifier_rejects_runtime_network_token(tmp_path: Path) -> None:
    verifier = _load_verifier()
    shell_path = ROOT / "apps/control-center/src/components/messenger/MessengerShell.tsx"
    relative = shell_path.relative_to(ROOT)
    destination = tmp_path / relative
    destination.parent.mkdir(parents=True)

    for required in (
        "apps/control-center/src/components/messenger/messengerShell.css",
        "apps/control-center/src/messenger/contracts.ts",
        "apps/control-center/src/messenger/fixtures.ts",
        "apps/control-center/src/components/messenger/MessengerShell.test.tsx",
        "apps/control-center/src/App.tsx",
        "apps/control-center/src/routes.tsx",
        "apps/control-center/package.json",
        "apps/control-center/package-lock.json",
        "docs/control_center/release_surface_manifest.json",
    ):
        source = ROOT / required
        target = tmp_path / required
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())

    destination.write_text(
        shell_path.read_text(encoding="utf-8") + "\nvoid fetch('/unsafe');\n",
        encoding="utf-8",
    )

    failures = verifier.verify(tmp_path)

    assert any("forbidden Messenger runtime token" in failure for failure in failures)
