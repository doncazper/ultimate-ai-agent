import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_current_baseline.py"


def load_verifier() -> Any:
    spec = importlib.util.spec_from_file_location("verify_current_baseline", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_frontend_package_files(
    root: Path,
    *,
    package_version: str,
    lock_version: str,
    root_lock_version: str,
) -> None:
    app_root = root / "apps/control-center"
    app_root.mkdir(parents=True)
    (app_root / "package.json").write_text(
        json.dumps(
            {
                "name": "@ultimate-ai-agent/control-center",
                "version": package_version,
            }
        ),
        encoding="utf-8",
    )
    (app_root / "package-lock.json").write_text(
        json.dumps(
            {
                "name": "@ultimate-ai-agent/control-center",
                "version": lock_version,
                "lockfileVersion": 3,
                "packages": {
                    "": {
                        "name": "@ultimate-ai-agent/control-center",
                        "version": root_lock_version,
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def test_current_baseline_verifier_accepts_matching_frontend_package_versions(tmp_path: Path) -> None:
    verifier = load_verifier()
    write_frontend_package_files(
        tmp_path,
        package_version="0.104.0",
        lock_version="0.104.0",
        root_lock_version="0.104.0",
    )

    assert verifier.verify_frontend_package_versions(tmp_path, "0.104.0") == []


def test_current_baseline_verifier_rejects_frontend_package_version_drift(tmp_path: Path) -> None:
    verifier = load_verifier()
    write_frontend_package_files(
        tmp_path,
        package_version="0.102.3",
        lock_version="0.102.3",
        root_lock_version="0.102.3",
    )

    failures = verifier.verify_frontend_package_versions(tmp_path, "0.104.0")

    assert any("package.json version (0.102.3)" in failure for failure in failures)
    assert any("package-lock.json version (0.102.3)" in failure for failure in failures)
    assert any("packages[''].version (0.102.3)" in failure for failure in failures)
