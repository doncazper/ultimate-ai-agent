#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = Path(".venv/bin/python")
CREATE_VENV_COMMAND = "python3 -m venv .venv"
INSTALL_DEV_COMMAND = '.venv/bin/python -m pip install -e ".[dev]"'


def _remediation() -> str:
    return f"Run: {CREATE_VENV_COMMAND}; then {INSTALL_DEV_COMMAND}"


def _python_version(python_path: Path) -> str:
    return subprocess.check_output([str(python_path), "--version"], cwd=ROOT, text=True).strip()


def _python_module_available(python_path: Path, module_name: str, root: Path = ROOT) -> bool:
    env = os.environ.copy()
    src_path = str(root / "src")
    env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
    result = subprocess.run(
        [str(python_path), "-c", f"import {module_name}"],
        cwd=root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return result.returncode == 0


def verify(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    python_path = root / VENV_PYTHON

    print("=== Ultimate AI Agent Developer Environment Verification ===")
    print(f"repo: {root}")
    print(f"python: {VENV_PYTHON}")

    if not python_path.exists():
        failures.append(f"{VENV_PYTHON} is missing. {_remediation()}")
        return failures

    try:
        print(f"python version: {_python_version(python_path)}")
    except (OSError, subprocess.SubprocessError) as exc:
        failures.append(f"could not run {VENV_PYTHON}: {exc}. {_remediation()}")
        return failures

    if _python_module_available(python_path, "ultimate_ai_agent", root):
        print("ultimate_ai_agent import: OK")
    else:
        failures.append(f"ultimate_ai_agent import failed. {_remediation()}")

    if _python_module_available(python_path, "pytest", root):
        print("pytest: OK")
    else:
        failures.append(f"pytest is unavailable. {_remediation()}")

    if _python_module_available(python_path, "ruff", root):
        print("ruff: OK")
    else:
        failures.append(f"ruff is unavailable. {_remediation()}")

    app_root = root / "apps/control-center"
    if app_root.exists():
        package_json = app_root / "package.json"
        if package_json.exists():
            print("control-center package.json: OK")
        else:
            failures.append("apps/control-center exists but package.json is missing")
        if shutil.which("npm"):
            print("npm: OK")
        else:
            print("npm: WARN unavailable; frontend checks need npm when required by repo convention")

    return failures


def main() -> int:
    failures = verify(ROOT)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("Developer environment verification PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
