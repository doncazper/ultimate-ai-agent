from pathlib import Path

import pytest

from ultimate_ai_agent.core.gate import FoundationGateEvaluator
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluation_context import _GateCachedText


@pytest.mark.parametrize(
    ("source", "needle"),
    [
        ("", ""),
        ("", "absent"),
        ("AuthorityToken", "Token"),
        ("AuthorityToken", "token"),
        ("aaab", "aab"),
        ("caf\u00e9 \U0001f98a", "\u00e9"),
        ("caf\u00e9 \U0001f98a", "e\u0301"),
        ("line\nend", "\n"),
        ("a\x00b", "\x00"),
    ],
)
def test_cached_text_membership_matches_native_string(source: str, needle: str) -> None:
    text = _GateCachedText(source)
    expected = str.__contains__(source, needle)

    for _ in range(3):
        assert (needle in text) is expected
    assert text._contains_cache == {needle: expected}


@pytest.mark.parametrize("needle", [None, 1, b"a", []])
def test_cached_text_preserves_native_non_string_errors(needle: object) -> None:
    text = _GateCachedText("safe source")

    with pytest.raises(TypeError) as native:
        str.__contains__("safe source", needle)
    with pytest.raises(TypeError) as cached:
        text.__contains__(needle)
    assert str(cached.value) == str(native.value)
    assert text._contains_cache == {}


def test_cached_text_misses_do_not_raise_and_false_results_are_reused() -> None:
    class ObservedCache(dict[str, bool]):
        def __init__(self) -> None:
            super().__init__()
            self.miss_exceptions = 0
            self.writes: list[tuple[str, bool]] = []

        def __missing__(self, key: str) -> bool:
            self.miss_exceptions += 1
            raise KeyError(key)

        def __setitem__(self, key: str, value: bool) -> None:
            self.writes.append((key, value))
            super().__setitem__(key, value)

    text = _GateCachedText("present")
    cache = ObservedCache()
    text._contains_cache = cache

    for _ in range(3):
        assert "present" in text
        assert "absent" not in text
    assert cache.writes == [("present", True), ("absent", False)]
    assert cache.miss_exceptions == 0


def test_cached_text_instances_and_lowercase_results_remain_separate() -> None:
    original = _GateCachedText("SCOPE \u0130\u00df")
    other = _GateCachedText("scope")
    lowered = original.lower()

    assert lowered == str(original).lower()
    assert lowered is original.lower()
    assert "scope" not in original
    assert "scope" in other
    assert "scope" in lowered
    assert original._contains_cache is not other._contains_cache
    assert original._contains_cache is not lowered._contains_cache


def test_cached_text_keeps_only_fixed_per_instance_cache_fields() -> None:
    text = _GateCachedText("scope")

    assert not hasattr(text, "__dict__")
    assert not hasattr(text.lower(), "__dict__")
    assert text._contains_cache == {}
    assert "scope" in text
    assert text._contains_cache == {"scope": True}


def test_each_evaluation_rechecks_changed_source(tmp_path: Path) -> None:
    source = tmp_path / "src/ultimate_ai_agent/core/example.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "shell_execution_absent"
    )
    evaluator = FoundationGateEvaluator(tmp_path)

    first = evaluator.evaluate([criterion])
    first_context = evaluator._context
    first_text = evaluator._read(source)
    assert first.results[0].status == "passed"
    assert "subprocess.run(" not in first_text

    source.write_text("import subprocess\nsubprocess.run(['safe-ref'])\n", encoding="utf-8")
    second = evaluator.evaluate([criterion])

    assert second.results[0].status == "failed"
    assert evaluator._context is not first_context
    assert "subprocess.run(" in evaluator._read(source)
    assert "subprocess.run(" not in first_text


@pytest.mark.parametrize("count", [0, 1, 255, 256, 257, 1000])
def test_true_assignment_index_preserves_late_matches_and_overflow(count: int) -> None:
    source = "other=True;" * count + "target=True"
    text = _GateCachedText(source)

    for needle in ("target=True", "absent=True", "other=True", "=True"):
        for _ in range(2):
            assert (needle in text) is str.__contains__(source, needle)
    assert text._true_assignment_ends is not None
    assert len(text._true_assignment_ends) == min(count + 1, 257)


def test_true_assignment_index_matches_native_substrings_without_token_rules() -> None:
    parts = (
        "", "a", "a=", "a=Tru", "=True", "\x00", "\u03b1", "\U0001f98a", "\ud800"
    )
    needles = (
        "a=True", "x=True", "=True=True", "a=Truea=True", "\u03b1=True",
        "\x00=True", "\ud800=True", "a=true", "a=\nTrue",
    )
    for prefix in parts:
        for suffix in parts:
            source = prefix + "=True" + suffix
            text = _GateCachedText(source)
            for needle in needles:
                assert (needle in text) is str.__contains__(source, needle)


def test_true_assignment_index_ignores_needle_subclass_method_overrides() -> None:
    class MisleadingNeedle(str):
        def __len__(self) -> int:
            return 0

        def endswith(self, *args: object) -> bool:
            return False

    source = "prefix_target=True_suffix"
    text = _GateCachedText(source)
    for needle in (MisleadingNeedle("target=True"), MisleadingNeedle("absent=True")):
        assert (needle in text) is str.__contains__(source, needle)
    assert text._true_assignment_ends is None
    assert text._contains_cache == {}


def test_true_assignment_empty_index_and_false_results_are_reused() -> None:
    text = _GateCachedText("no matching suffix")
    assert "first=True" not in text
    first_index = text._true_assignment_ends
    assert first_index == ()
    assert "second=True" not in text
    assert "first=True" not in text
    assert text._true_assignment_ends is first_index
    assert text._contains_cache == {"first=True": False, "second=True": False}


def test_true_assignment_indexes_do_not_cross_text_or_lowercase_boundaries() -> None:
    first = _GateCachedText("target=True")
    second = _GateCachedText("other=True")
    lowered = first.lower()
    assert "target=True" in first
    assert "target=True" not in second
    assert "target=True" not in lowered
    assert "target=true" in lowered
    assert first._true_assignment_ends == (11,)
    assert second._true_assignment_ends == (10,)
    assert lowered._true_assignment_ends == ()


def test_string_subclass_hash_and_equality_cannot_poison_membership_cache() -> None:
    class UnhashableNeedle(str):
        __hash__ = None

    class AliasingNeedle(str):
        def __hash__(self) -> int:
            return hash("target=True")

        def __eq__(self, other: object) -> bool:
            return True

    source = "target=True"
    text = _GateCachedText(source)
    assert "target=True" in text
    for needle in (UnhashableNeedle("target=True"), AliasingNeedle("absent=True")):
        assert (needle in text) is str.__contains__(source, needle)
    assert text._contains_cache == {"target=True": True}


def test_true_assignment_index_refreshes_after_source_changes(tmp_path: Path) -> None:
    source = tmp_path / "src/ultimate_ai_agent/core/example.py"
    source.parent.mkdir(parents=True)
    source.write_text("flag=False\n", encoding="utf-8")
    criterion = next(
        item for item in default_foundation_gate_criteria()
        if item.criterion_id == "shell_execution_absent"
    )
    evaluator = FoundationGateEvaluator(tmp_path)
    assert evaluator.evaluate([criterion]).results[0].status == "passed"
    before = evaluator._read(source)
    assert "flag=True" not in before
    assert before._true_assignment_ends == ()

    source.write_text("flag=True\n", encoding="utf-8")
    assert evaluator.evaluate([criterion]).results[0].status == "passed"
    after = evaluator._read(source)
    assert "flag=True" in after
    assert after._true_assignment_ends == (9,)
    assert "flag=True" not in before
