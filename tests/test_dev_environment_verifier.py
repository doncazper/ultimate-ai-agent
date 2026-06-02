import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_dev_environment.py"
MAKEFILE = ROOT / "Makefile"


def load_verifier():
    spec = importlib.util.spec_from_file_location("verify_dev_environment", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_dev_environment_verifier_passes_current_repo(capsys):
    verifier = load_verifier()

    assert verifier.verify(ROOT) == []
    output = capsys.readouterr().out

    assert ".venv/bin/python" in output
    assert "ultimate_ai_agent import: OK" in output
    assert "pytest: OK" in output
    assert "ruff: OK" in output


def test_dev_environment_verifier_reports_clear_remediation_for_missing_venv(tmp_path):
    verifier = load_verifier()

    failures = verifier.verify(tmp_path)

    assert any(".venv/bin/python is missing" in failure for failure in failures)
    assert any("python3 -m venv .venv" in failure for failure in failures)
    assert any('.venv/bin/python -m pip install -e ".[dev]"' in failure for failure in failures)


def test_dev_environment_verifier_warns_without_failing_when_npm_is_missing(tmp_path, monkeypatch, capsys):
    verifier = load_verifier()
    app_root = tmp_path / "apps/control-center"
    app_root.mkdir(parents=True)
    (app_root / "package.json").write_text("{}", encoding="utf-8")
    venv_python = tmp_path / ".venv/bin/python"
    venv_python.parent.mkdir(parents=True)
    venv_python.write_text("", encoding="utf-8")

    monkeypatch.setattr(verifier, "_python_version", lambda path: "Python 3.12.0")
    monkeypatch.setattr(verifier, "_python_module_available", lambda path, module_name, root=None: True)
    monkeypatch.setattr(verifier.shutil, "which", lambda command: None if command == "npm" else command)

    assert verifier.verify(tmp_path) == []
    output = capsys.readouterr().out

    assert "npm: WARN" in output


def test_makefile_uses_project_venv_python_for_verification_commands():
    text = MAKEFILE.read_text(encoding="utf-8")

    for target in ["doctor:", "test:", "verify:", "frontend-check:", "openapi:", "ruff:"]:
        assert target in text
    assert "PYTHON := .venv/bin/python" in text
    assert "PYTHONPATH=src $(PYTHON) -m pytest" in text
    assert "$(PYTHON) scripts/verify_current_baseline.py" in text
    assert "$(PYTHON) scripts/run_foundation_gate.py" in text
    assert "$(PYTHON) -m ruff check ." in text
    assert "python scripts/" not in text
