from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
SEED_BUILDER = ROOT / "scripts/verification/build_pytest_timing_seed.py"


def load_seed_builder() -> Any:
    spec = importlib.util.spec_from_file_location(
        "build_pytest_timing_seed", SEED_BUILDER
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_timing_seed_builder_emits_only_allowlisted_advisory_entries(
    tmp_path: Path,
) -> None:
    builder = load_seed_builder()
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    unsafe = "/Users/private/raw-secret-prompt.txt"
    (log_dir / "pytest-shard-0.log").write_text(
        "\n".join(
            [
                "1.25s call tests/test_api.py::test_one",
                f"99.00s call {unsafe}::test_leak",
            ]
        ),
        encoding="utf-8",
    )
    (log_dir / "pytest-shard-1.log").write_text(
        "2.75s setup tests/test_api.py::test_two\n", encoding="utf-8"
    )

    payload = builder.build_seed(log_dir, source_run_status="green")

    assert payload["advisory_only"] is True
    assert payload["verification_evidence"] is False
    assert payload["declared_source_run_status"] == "green"
    assert payload["source_run_status_attestation"] == "operator_supplied_advisory"
    assert payload["timed_file_count"] == 1
    assert payload["timings"] == [
        {
            "path": "tests/test_api.py",
            "seconds": 4.0,
            "source": "historical-pytest-duration-summary",
        }
    ]
    assert unsafe not in json.dumps(payload)


def test_timing_seed_builder_rejects_missing_or_empty_duration_logs(
    tmp_path: Path,
) -> None:
    builder = load_seed_builder()
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    with pytest.raises(ValueError, match="PYTEST_TIMING_SEED_LOGS_REQUIRED"):
        builder.build_seed(log_dir, source_run_status="green")

    (log_dir / "pytest-shard-0.log").write_text(
        "raw prompt and local path are not timing rows\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="PYTEST_TIMING_SEED_DURATIONS_REQUIRED"):
        builder.build_seed(log_dir, source_run_status="completed_with_failures")
