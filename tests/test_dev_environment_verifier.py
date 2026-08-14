from typing import Any
import pytest
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_dev_environment.py"
MAKEFILE = ROOT / "Makefile"


def make_target_body(text: str, target: str) -> list[str]:
    lines = text.splitlines()
    start = lines.index(f"{target}:") + 1
    body: list[str] = []
    for line in lines[start:]:
        if line and not line.startswith("\t"):
            break
        if line.startswith("\t"):
            body.append(line.strip())
    return body


def load_verifier() -> Any:
    spec = importlib.util.spec_from_file_location("verify_dev_environment", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_dev_environment_verifier_passes_current_repo(
    capsys: pytest.CaptureFixture[str],
) -> None:
    verifier = load_verifier()

    assert verifier.verify(ROOT) == []
    output = capsys.readouterr().out

    assert ".venv/bin/python" in output
    assert "ultimate_ai_agent import: OK" in output
    assert "pytest: OK" in output
    assert "ruff: OK" in output


def test_dev_environment_verifier_reports_clear_remediation_for_missing_venv(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()

    failures = verifier.verify(tmp_path)

    assert any(".venv/bin/python is missing" in failure for failure in failures)
    assert any("python3 -m venv .venv" in failure for failure in failures)
    assert any(
        '.venv/bin/python -m pip install -e ".[dev]"' in failure for failure in failures
    )


def test_dev_environment_verifier_warns_without_failing_when_npm_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    verifier = load_verifier()
    app_root = tmp_path / "apps/control-center"
    app_root.mkdir(parents=True)
    (app_root / "package.json").write_text("{}", encoding="utf-8")
    venv_python = tmp_path / ".venv/bin/python"
    venv_python.parent.mkdir(parents=True)
    venv_python.write_text("", encoding="utf-8")

    monkeypatch.setattr(verifier, "_python_version", lambda path: "Python 3.12.0")
    monkeypatch.setattr(
        verifier, "_python_module_available", lambda path, module_name, root=None: True
    )
    monkeypatch.setattr(
        verifier.shutil, "which", lambda command: None if command == "npm" else command
    )

    assert verifier.verify(tmp_path) == []
    output = capsys.readouterr().out

    assert "npm: WARN" in output


def test_makefile_uses_project_venv_python_for_verification_commands() -> None:
    text = MAKEFILE.read_text(encoding="utf-8")

    for target in [
        "doctor:",
        "test:",
        "test-serial:",
        "test-sharded:",
        "test-sharded-profile:",
        "verify:",
        "verify-static:",
        "verify-gate-architecture:",
        "verify-fast:",
        "verify-affected:",
        "verify-value-audit:",
        "verify-dev-fast:",
        "verify-local:",
        "frontend-check:",
        "openapi:",
        "ruff:",
    ]:
        assert target in text
    assert "PYTHON := .venv/bin/python" in text
    assert "VERIFY_TIMINGS_JSON ?= /tmp/uaa_verify_all_timings.json" in text
    assert "VERIFY_DEV_FAST_JOBS ?= 4" in text
    assert "PYTEST_SHARD_WORKERS ?= 4" in text
    assert "PYTHONPATH=src $(PYTHON) -m pytest" in text
    assert "$(PYTHON) scripts/verification/run_static_verification_lane.py" in text
    assert (
        "$(PYTHON) scripts/verification/run_static_verification_lane.py "
        "--skip-ruff --skip-pytest --timings-json $(VERIFY_TIMINGS_JSON)" in text
    )
    assert (
        "$(MAKE) -j$(VERIFY_DEV_FAST_JOBS) ruff test verify-static verify-gate-architecture"
        in text
    )
    assert "verify-local: verify-dev-sharded" in text
    assert "PYTHONPATH=src $(PYTHON) scripts/verify_gate_architecture.py" in text
    assert "$(PYTHON) scripts/run_foundation_gate.py --command-mode report-only" in text
    assert (
        "$(PYTHON) scripts/run_foundation_gate.py --command-mode report-only --no-write-latest"
        in text
    )
    assert "$(PYTHON) -m ruff check ." in text
    assert "python scripts/" not in text


def test_make_verify_runs_full_sharded_release_gate_and_preserves_serial_diagnostics() -> (
    None
):
    text = MAKEFILE.read_text(encoding="utf-8")

    verify_body = make_target_body(text, "verify")
    assert verify_body == [
        "$(MAKE) ruff test-sharded verify-static",
        "PYTHONPATH=src $(PYTHON) scripts/verify_gate_architecture.py",
        "$(PYTHON) scripts/run_foundation_gate.py --command-mode report-only",
    ]
    assert not any(
        "verify-dev-fast" in line or "-j$(VERIFY_DEV_FAST_JOBS)" in line
        for line in verify_body
    )

    verify_dev_fast_body = make_target_body(text, "verify-dev-fast")
    assert verify_dev_fast_body == [
        "$(MAKE) -j$(VERIFY_DEV_FAST_JOBS) ruff test verify-static verify-gate-architecture",
        "$(PYTHON) scripts/run_foundation_gate.py --command-mode report-only --no-write-latest",
    ]
    assert not any(
        "verify " in line or "scripts/verify_all.py" in line
        for line in verify_dev_fast_body
    )
    assert make_target_body(text, "test") == ["$(MAKE) test-sharded"]
    assert make_target_body(text, "test-serial") == [
        "PYTHONPATH=src $(PYTHON) -m pytest"
    ]


def test_verification_bootstrap_installs_every_frozen_local_runtime() -> None:
    text = MAKEFILE.read_text(encoding="utf-8")

    assert make_target_body(text, "verification-bootstrap") == [
        "python3.12 -m venv .ci-bootstrap",
        '.ci-bootstrap/bin/python -m pip install --disable-pip-version-check "uv==0.11.21"',
        ".ci-bootstrap/bin/uv sync --frozen --extra dev --python python3.12",
        "npm --prefix integrations/matrix-client-adapter ci --ignore-scripts",
        "npm --prefix apps/control-center ci --ignore-scripts",
    ]
