from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verification/run_dev_fast_gate.py"
MAKEFILE = ROOT / "Makefile"


def load_gate() -> Any:
    spec = importlib.util.spec_from_file_location("run_dev_fast_gate", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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


def test_make_verify_keeps_full_proof_with_sharded_pytest_and_summary_runner() -> None:
    text = MAKEFILE.read_text(encoding="utf-8")

    assert make_target_body(text, "verify") == [
        "$(MAKE) ruff test-sharded verify-static",
        "PYTHONPATH=src $(PYTHON) scripts/verify_gate_architecture.py",
        "$(PYTHON) scripts/run_foundation_gate.py --command-mode report-only",
    ]
    dev_sharded_body = make_target_body(text, "verify-dev-sharded")
    assert "scripts/verification/run_dev_fast_gate.py" in " ".join(dev_sharded_body)
    assert "--pytest-shards $(PYTEST_SHARDS)" in " ".join(dev_sharded_body)
    assert "--pytest-workers $(PYTEST_SHARD_WORKERS)" in " ".join(dev_sharded_body)
    assert "--pytest-timing-seed-json $(PYTEST_SHARD_TIMING_SEED_JSON)" in " ".join(
        dev_sharded_body
    )
    assert "--static-timings-json $(VERIFY_TIMINGS_JSON)" in " ".join(dev_sharded_body)
    assert "--no-write-latest" not in make_target_body(text, "verify")[2]


def test_fast_gate_parallel_phases_keep_required_contract_checks(
    tmp_path: Path,
) -> None:
    gate = load_gate()
    args = gate.parse_args(
        [
            "--jobs",
            "2",
            "--pytest-shards",
            "2",
            "--pytest-workers",
            "1",
            "--pytest-timings-json",
            str(tmp_path / "pytest.json"),
            "--pytest-timing-seed-json",
            str(tmp_path / "seed.json"),
            "--pytest-basetemp",
            str(tmp_path / "pytest-tmp"),
            "--static-timings-json",
            str(tmp_path / "static.json"),
            "--timings-json",
            str(tmp_path / "summary.json"),
        ]
    )

    phases = gate.build_parallel_phases(args)
    phase_by_name = {phase.name: phase for phase in phases}

    assert set(phase_by_name) == {
        "ruff",
        "pytest-sharded",
        "static-verification",
        "gate-architecture",
    }
    static_command = phase_by_name["static-verification"].command
    assert "scripts/verify_all.py" in static_command
    assert "--skip-ruff" in static_command
    assert "--skip-pytest" in static_command
    assert "--skip-openapi" not in static_command
    assert "--skip-docs" not in static_command
    assert "--skip-static-scans" not in static_command
    assert (
        "scripts/verify_gate_architecture.py"
        in phase_by_name["gate-architecture"].command
    )
    assert (
        "scripts/verification/run_pytest_shards.py"
        in phase_by_name["pytest-sharded"].command
    )
    assert str(tmp_path / "seed.json") in phase_by_name["pytest-sharded"].command
    assert "--max-workers" in phase_by_name["pytest-sharded"].command
    assert "1" in phase_by_name["pytest-sharded"].command
    assert "UAA_M160_LIVE_HF_GGUF_SEARCH" not in (
        phase_by_name["pytest-sharded"].env or {}
    )


def test_foundation_gate_is_serial_report_only_no_write() -> None:
    gate = load_gate()

    phases = gate.build_serial_phases()

    assert len(phases) == 1
    phase = phases[0]
    assert phase.parallel is False
    assert "scripts/run_foundation_gate.py" in phase.command
    assert "--command-mode" in phase.command
    assert "report-only" in phase.command
    assert "--no-write-latest" in phase.command


def test_fast_gate_writes_safe_timing_summary(tmp_path: Path) -> None:
    gate = load_gate()
    log_path = tmp_path / "phase.log"
    log_path.write_text("ok\n", encoding="utf-8")
    result = gate.PhaseResult(
        name="pytest-sharded",
        command_ref="command:pytest-sharded",
        command=("python", "-m", "pytest"),
        status="passed",
        elapsed_seconds=1.25,
        returncode=0,
        log_path=log_path,
    )
    timings_path = tmp_path / "timings.json"

    gate.write_timing_summary(timings_path, [result], total_elapsed_seconds=1.5)

    payload = json.loads(timings_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "uaa_verify_dev_fast_gate_timings.v1"
    assert payload["release_gate"] is False
    assert payload["summary"]["overall_status"] == "passed"
    assert payload["summary"]["total_elapsed_seconds"] == 1.5
    assert payload["summary"]["phase_elapsed_seconds_sum"] == 1.25
    assert payload["phases"][0]["command_ref"] == "command:pytest-sharded"
    assert payload["phases"][0]["status"] == "passed"


def test_static_timing_count_reads_verify_all_timings(tmp_path: Path) -> None:
    gate = load_gate()
    timing_path = tmp_path / "static.json"
    timing_path.write_text(
        json.dumps(
            {
                "schema_version": "verify_all_timings.v1",
                "timings": [
                    {"name": "static_scan:one", "elapsed_ms": 1, "status": "passed"},
                    {
                        "name": "command:verify_openapi_contract",
                        "elapsed_ms": 2,
                        "status": "passed",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    assert gate.static_timing_count(timing_path) == 2
