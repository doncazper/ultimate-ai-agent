import json

import pytest

import scripts.benchmark_foundation_gate as benchmark_foundation_gate
import scripts.check_foundation_gate_latency as check_foundation_gate_latency


class _FakeReport:
    overall_status = "passed"
    results = ("criterion:one", "criterion:two")


def test_foundation_gate_benchmark_emits_parseable_metrics(monkeypatch):
    monkeypatch.setattr(benchmark_foundation_gate, "_evaluate_once", lambda: _FakeReport())

    metrics = benchmark_foundation_gate._benchmark(repeat=2, warmup=1)

    assert metrics["schema_version"] == "foundation_gate_benchmark.v1"
    assert metrics["repeat"] == 2
    assert metrics["warmup"] == 1
    assert metrics["foundation_gate_status"] == "passed"
    assert metrics["foundation_gate_result_count"] == 2
    assert len(metrics["foundation_gate_runs_ms"]) == 2


def test_foundation_gate_latency_guard_emits_parseable_metrics(monkeypatch, capsys):
    def fake_benchmark(*, repeat: int, warmup: int):
        return {
            "schema_version": "foundation_gate_benchmark.v1",
            "repeat": repeat,
            "warmup": warmup,
            "foundation_gate_runs_ms": [10.0],
            "foundation_gate_best_ms": 10.0,
            "foundation_gate_mean_ms": 10.0,
            "foundation_gate_status": "passed",
            "foundation_gate_result_count": 2,
        }

    monkeypatch.setattr(benchmark_foundation_gate, "_benchmark", fake_benchmark)

    exit_code = check_foundation_gate_latency.main(
        [
            "--repeat",
            "1",
            "--max-best-ms",
            "1000",
            "--max-mean-ms",
            "1000",
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is True
    assert payload["failures"] == []
    assert payload["foundation_gate_mean_ms"] == 10.0


def test_foundation_gate_latency_guard_fails_when_budget_exceeded(monkeypatch, capsys):
    def fake_benchmark(*, repeat: int, warmup: int):
        return {
            "schema_version": "foundation_gate_benchmark.v1",
            "repeat": repeat,
            "warmup": warmup,
            "foundation_gate_runs_ms": [1500.0],
            "foundation_gate_best_ms": 1500.0,
            "foundation_gate_mean_ms": 1500.0,
            "foundation_gate_status": "passed",
            "foundation_gate_result_count": 2,
        }

    monkeypatch.setattr(benchmark_foundation_gate, "_benchmark", fake_benchmark)

    exit_code = check_foundation_gate_latency.main(
        [
            "--repeat",
            "1",
            "--max-best-ms",
            "1000",
            "--max-mean-ms",
            "1000",
            "--json",
        ]
    )

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is False
    assert "best 1500.00 ms exceeds budget 1000.00 ms" in payload["failures"]
    assert "mean 1500.00 ms exceeds budget 1000.00 ms" in payload["failures"]


def test_foundation_gate_latency_guard_rejects_invalid_env_budget(monkeypatch):
    monkeypatch.setenv("FOUNDATION_GATE_MAX_MEAN_MS", "not-a-number")

    with pytest.raises(SystemExit) as exc:
        check_foundation_gate_latency.main(["--json"])

    assert exc.value.code == 2
