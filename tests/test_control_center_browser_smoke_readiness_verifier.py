import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_control_center_browser_smoke_readiness.py"


def load_verifier():
    spec = importlib.util.spec_from_file_location("verify_control_center_browser_smoke_readiness", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_control_center_browser_smoke_readiness_verifier_passes_current_repo():
    verifier = load_verifier()

    assert verifier.verify(ROOT) == []


def test_control_center_browser_smoke_readiness_verifier_blocks_unsafe_ci_and_docs(tmp_path):
    (tmp_path / ".github/workflows").mkdir(parents=True)
    (tmp_path / "apps/control-center").mkdir(parents=True)
    (tmp_path / "docs/control_center").mkdir(parents=True)
    (tmp_path / ".github/workflows/ci.yml").write_text(
        "jobs:\n  smoke:\n    steps:\n      - run: npx playwright test https://example.com\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/package.json").write_text(
        '{"scripts":{"dev":"vite --host 127.0.0.1","preview":"vite preview --host 127.0.0.1"}}',
        encoding="utf-8",
    )
    (tmp_path / "docs/control_center/LOCAL_BROWSER_SMOKE.md").write_text(
        "Use Chrome authenticated profile control against production.\n",
        encoding="utf-8",
    )
    (tmp_path / "docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md").write_text(
        "Local browser smoke report may include screenshots with secrets.\n",
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("forbidden CI browser automation fragment" in failure for failure in failures)
    assert any("smoke doc missing required safety wording" in failure for failure in failures)
    assert any("smoke reporting doc missing required safety wording" in failure for failure in failures)
    assert any("forbidden smoke doc fragment" in failure for failure in failures)
