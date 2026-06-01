import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_control_center_frontend.py"


def load_verifier():
    spec = importlib.util.spec_from_file_location("verify_control_center_frontend", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_control_center_frontend_verifier_passes_current_repo():
    verifier = load_verifier()

    assert verifier.verify(ROOT) == []


def test_control_center_frontend_verifier_blocks_forbidden_frontend_strings(tmp_path):
    app_root = tmp_path / "apps/control-center"
    (app_root / "src/api").mkdir(parents=True)
    (app_root / "src/mocks").mkdir(parents=True)
    (app_root / "src/components").mkdir(parents=True)
    (app_root / "package.json").write_text('{"dependencies":{"react":"1.0.0"}}', encoding="utf-8")
    (app_root / "package-lock.json").write_text("{}", encoding="utf-8")
    (app_root / "src/api/endpoints.ts").write_text(
        'export const API_ENDPOINTS = { actionPreview: "/control-center/actions/preview" } as const;\n',
        encoding="utf-8",
    )
    (app_root / "src/mocks/controlCenterData.ts").write_text(
        "export const mockControlCenterData = { mock: true, production_ready: false };\n",
        encoding="utf-8",
    )
    (app_root / "src/components/ActionPreviewForm.tsx").write_text(
        'export function ActionPreviewForm() { return <button>Execute</button>; }\n',
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("dangerous action control label" in failure for failure in failures)
