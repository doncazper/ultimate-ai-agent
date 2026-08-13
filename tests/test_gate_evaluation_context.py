from pathlib import Path

from ultimate_ai_agent.core.gate import FoundationGateEvaluator
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate import legacy_support


def test_evaluator_read_uses_cached_file_classification(
    tmp_path: Path,
    monkeypatch,
) -> None:
    existing = tmp_path / "src/ultimate_ai_agent/core/example.py"
    existing.parent.mkdir(parents=True)
    existing.write_text("VALUE = 1\n", encoding="utf-8")
    missing = existing.with_name("missing.py")
    evaluator = FoundationGateEvaluator(tmp_path)

    def unexpected_exists(self: Path) -> bool:
        raise AssertionError("cached evaluator reads must not repeat Path.exists()")

    monkeypatch.setattr(Path, "exists", unexpected_exists)

    assert evaluator._read(existing) == "VALUE = 1\n"
    assert evaluator._read(existing) == "VALUE = 1\n"
    assert evaluator._read(missing) == ""
    assert evaluator._read(missing) == ""


def test_runtime_subprocess_allowance_cache_is_bound_to_exact_source(
    monkeypatch,
) -> None:
    calls = 0

    def exact_adapter_check(rel: str, source: str, fragment: str) -> bool:
        nonlocal calls
        calls += 1
        return True

    monkeypatch.setattr(legacy_support, "sealed_fragment_allowed", exact_adapter_check)
    legacy_support.runtime_subprocess_fragment_allowed.cache_clear()

    assert legacy_support.runtime_subprocess_fragment_allowed(
        "safe.py",
        "source-v1",
        "fragment",
    )
    assert legacy_support.runtime_subprocess_fragment_allowed(
        "safe.py",
        "source-v1",
        "fragment",
    )
    assert legacy_support.runtime_subprocess_fragment_allowed(
        "safe.py",
        "source-v2",
        "fragment",
    )
    assert calls == 2


def test_runtime_safety_scans_read_each_source_once_per_criterion(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "src/ultimate_ai_agent/core/example.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\nVALUE = 2\nVALUE = 3\n", encoding="utf-8")
    criteria = {
        criterion.criterion_id: criterion
        for criterion in default_foundation_gate_criteria()
    }

    for criterion_id in (
        "forbidden_runtime_integrations_absent",
        "shell_execution_absent",
    ):
        evaluator = FoundationGateEvaluator(tmp_path)
        original_read = evaluator._read
        source_reads = 0

        def counted_read(path: Path, *, read=original_read) -> str:
            nonlocal source_reads
            if path == source:
                source_reads += 1
            return read(path)

        monkeypatch.setattr(evaluator, "_read", counted_read)
        result = getattr(evaluator, f"check_{criterion_id}")(criteria[criterion_id])

        assert result.status == "passed"
        assert source_reads == 2
