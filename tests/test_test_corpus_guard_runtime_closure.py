from pathlib import Path

import pytest

from scripts.verification import test_corpus_guard as guard


TEST_PATH = "tests/test_sample.py"
PACKAGE_PATH = "src/ultimate_ai_agent/__init__.py"
SUBJECT_PATH = "src/ultimate_ai_agent/subject.py"
CHILD_PATH = "src/ultimate_ai_agent/new_child.py"
GRANDCHILD_PATH = "src/ultimate_ai_agent/new_grandchild.py"
BASE_SHA = "a" * 40


def _write_sources(root: Path, sources: dict[str, str]) -> None:
    for path, source in sources.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")


def _install_subject(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_source: str,
    *,
    base_subject: str = "def runtime_value(): return 1\n",
    current_subject: str = ("from ultimate_ai_agent.new_child import runtime_value\n"),
    additions: dict[str, str] | None = None,
    base_additions: dict[str, str] | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    base = {
        TEST_PATH: test_source,
        PACKAGE_PATH: "",
        SUBJECT_PATH: base_subject,
        # The real comparison base already completed both historical identity
        # migrations. Omitting this posture exercises a different migration.
        guard.TEST_CORPUS_GUARD_PATH: "\n".join(
            (
                "# " + guard.PARAMETER_DEPENDENCY_IDENTITY_MIGRATION_MARKER,
                "# " + guard.PYTHON310_DEPENDENCY_IDENTITY_MIGRATION_MARKER,
            )
        ),
        **(base_additions or {}),
    }
    current = {
        **base,
        SUBJECT_PATH: current_subject,
        **(
            {CHILD_PATH: "def runtime_value(): return 1\n"}
            if additions is None
            else additions
        ),
    }
    _write_sources(root, current)
    monkeypatch.setattr(guard, "discover_test_files", lambda _repo: (TEST_PATH,))
    monkeypatch.setattr(
        guard, "_changed_test_paths", lambda _repo, _base_sha: (TEST_PATH,)
    )
    monkeypatch.setattr(
        guard, "_base_file_paths", lambda _repo, _base_sha: frozenset(base)
    )
    monkeypatch.setattr(
        guard, "_base_text", lambda _repo, _base_sha, path: base.get(path)
    )
    return base, current


DIRECT_TEST = (
    "from ultimate_ai_agent.subject import runtime_value\n"
    "def test_case(): assert runtime_value() == 1\n"
)
AUTOUSE_TEST = (
    "import pytest\n"
    "from ultimate_ai_agent.subject import runtime_value\n"
    "@pytest.fixture(autouse=True)\n"
    "def fixture_value(): assert runtime_value() == 1\n"
    "def test_case(): assert True\n"
)
MODULE_AUTOUSE_TEST = (
    "import pytest\n"
    "import ultimate_ai_agent.subject as subject\n"
    "@pytest.fixture(autouse=True)\n"
    "def fixture_value(monkeypatch):\n"
    "    monkeypatch.setattr(subject, 'SENTINEL', 1)\n"
    "def test_case(): assert subject.runtime_value() == 1\n"
)
SKIP_HELPER_TEST = (
    "import pytest\n"
    "from ultimate_ai_agent.subject import runtime_value\n"
    "def require_value():\n"
    "    value = runtime_value()\n"
    "    if value is None: pytest.skip('unavailable')\n"
    "    return value\n"
    "def test_case(): assert require_value() == 1\n"
)


@pytest.mark.parametrize(
    "test_source",
    [DIRECT_TEST, AUTOUSE_TEST, MODULE_AUTOUSE_TEST, SKIP_HELPER_TEST],
    ids=["direct", "autouse", "module-autouse", "existing-skip-helper"],
)
@pytest.mark.parametrize("nested", [False, True], ids=["child", "grandchild"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_new_runtime_closure_preserves_unchanged_declarations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_source: str,
    nested: bool,
    snapshot: bool,
) -> None:
    additions = {CHILD_PATH: "def runtime_value(): return 1\n"}
    if nested:
        additions = {
            CHILD_PATH: (
                "from ultimate_ai_agent.new_grandchild import runtime_value\n"
            ),
            GRANDCHILD_PATH: "def runtime_value(): return 1\n",
        }
    _install_subject(tmp_path, monkeypatch, test_source, additions=additions)

    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None

    assert (
        guard.removed_declarations(tmp_path, BASE_SHA, worktree_snapshot=inventory)
        == ()
    )


@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_new_runtime_package_and_initializer_preserve_declarations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, snapshot: bool
) -> None:
    _install_subject(
        tmp_path,
        monkeypatch,
        AUTOUSE_TEST,
        current_subject="from ultimate_ai_agent.new_package import runtime_value\n",
        additions={
            "src/ultimate_ai_agent/new_package/__init__.py": (
                "from .child import runtime_value\n"
            ),
            "src/ultimate_ai_agent/new_package/child.py": (
                "def runtime_value(): return 1\n"
            ),
        },
    )

    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None

    assert (
        guard.removed_declarations(tmp_path, BASE_SHA, worktree_snapshot=inventory)
        == ()
    )


@pytest.mark.parametrize(
    "child_source",
    [
        "import pytest\npytest.skip('unavailable', allow_module_level=True)\n",
        "import pytest\npytest.importorskip('absent_fixture_module')\n",
        "from unittest import SkipTest\nraise SkipTest('unavailable')\n",
        "def runtime_value(:\n",
        "import importlib\nMODULE = unknown_name\nimportlib.import_module(MODULE)\n",
    ],
    ids=["pytest-skip", "importorskip", "unittest-skip", "malformed", "dynamic"],
)
def test_new_runtime_grandchild_rejects_unproven_collection_closure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, child_source: str
) -> None:
    _install_subject(
        tmp_path,
        monkeypatch,
        AUTOUSE_TEST,
        additions={
            CHILD_PATH: "from ultimate_ai_agent.new_grandchild import runtime_value\n",
            GRANDCHILD_PATH: child_source,
        },
    )

    with pytest.raises(guard.TestCorpusGuardError):
        guard.removed_declarations(tmp_path, BASE_SHA)


@pytest.mark.parametrize(
    "child_source",
    [
        "import pytest\ndef runtime_value(): pytest.skip('unavailable')\n",
        "from pytest import xfail as abort\ndef runtime_value(): abort('unavailable')\n",
        "import pytest\ndef runtime_value(): pytest.importorskip('absent_fixture_module')\n",
        "from unittest import SkipTest\ndef runtime_value(): raise SkipTest('unavailable')\n",
        "import unittest as unit\ndef runtime_value(): raise unit.SkipTest('unavailable')\n",
        "import pytest\nruntime_value = lambda: pytest.skip('unavailable')\n",
        "import pytest as checks\nabort = checks.skip\ndef runtime_value(): abort('unavailable')\n",
        "from unittest.case import SkipTest as Abort\ndef runtime_value(): raise Abort('unavailable')\n",
        "def runtime_value():\n    import pytest as checks\n    checks.skip('unavailable')\n",
        "import pytest\ndef runtime_value(): raise pytest.skip.Exception('unavailable')\n",
        "import pytest\nabort = getattr(pytest, 'skip')\ndef runtime_value(): abort('unavailable')\n",
        "def runtime_value():\n    checks = __import__('pytest')\n    checks.skip('unavailable')\n",
        "import importlib\ndef runtime_value():\n    checks = importlib.import_module('pytest')\n    checks.skip('unavailable')\n",
        "from importlib import import_module as load\nchecks = load('unittest')\ndef runtime_value(): raise checks.SkipTest('unavailable')\n",
        "from unittest import SkipTest\ndef runtime_value(): raise SkipTest\n",
        "import pytest\ndef runtime_value(): raise pytest.skip.Exception\n",
    ],
    ids=[
        "skip",
        "xfail-alias",
        "importorskip",
        "SkipTest",
        "SkipTest-namespace",
        "lambda",
        "callable-alias",
        "SkipTest-import-alias",
        "function-local-import",
        "skip-exception",
        "getattr-alias",
        "builtin-dynamic-import",
        "importlib-dynamic-import",
        "dynamic-unittest-alias",
        "SkipTest-reference",
        "skip-exception-reference",
    ],
)
def test_new_runtime_child_cannot_hide_execution_abort(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, child_source: str
) -> None:
    _install_subject(
        tmp_path,
        monkeypatch,
        AUTOUSE_TEST,
        additions={CHILD_PATH: child_source},
    )

    try:
        removed = guard.removed_declarations(tmp_path, BASE_SHA)
    except guard.TestCorpusGuardError:
        return
    assert len(removed) == 1
    assert "::autouse-sha256:" in removed[0]


@pytest.mark.parametrize("existed_at_base", [False, True])
def test_new_runtime_child_cannot_introduce_transitive_execution_abort(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, existed_at_base: bool
) -> None:
    abort_source = "import pytest\ndef runtime_value(): pytest.skip('unavailable')\n"
    _install_subject(
        tmp_path,
        monkeypatch,
        AUTOUSE_TEST,
        base_additions={GRANDCHILD_PATH: abort_source} if existed_at_base else {},
        additions={
            CHILD_PATH: "from ultimate_ai_agent.new_grandchild import runtime_value\n",
            GRANDCHILD_PATH: abort_source,
        },
    )

    try:
        removed = guard.removed_declarations(tmp_path, BASE_SHA)
    except guard.TestCorpusGuardError:
        return
    assert len(removed) == 1
    assert "::autouse-sha256:" in removed[0]


def test_new_runtime_child_rejects_ambiguous_module_and_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_subject(
        tmp_path,
        monkeypatch,
        AUTOUSE_TEST,
        additions={
            CHILD_PATH: "def runtime_value(): return 1\n",
            "src/ultimate_ai_agent/new_child/__init__.py": (
                "def runtime_value(): return 1\n"
            ),
        },
    )

    with pytest.raises(guard.TestCorpusGuardError, match="ambiguous"):
        guard.removed_declarations(tmp_path, BASE_SHA)


def test_new_runtime_child_does_not_replace_base_parameter_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = (
        "import pytest\n"
        "from ultimate_ai_agent.subject import VALUES, runtime_value\n"
        "@pytest.mark.parametrize('value', VALUES)\n"
        "def test_case(value): assert runtime_value() == value\n"
    )
    _install_subject(
        tmp_path,
        monkeypatch,
        source,
        base_subject="VALUES = (1, 2)\ndef runtime_value(): return 1\n",
        current_subject=(
            "from ultimate_ai_agent.new_child import VALUES, runtime_value\n"
        ),
        additions={CHILD_PATH: "VALUES = (1,)\ndef runtime_value(): return 1\n"},
    )

    removed = guard.removed_declarations(tmp_path, BASE_SHA)

    assert len(removed) == 1
    assert "::test_case::parametrize-sha256:" in removed[0]


def test_new_runtime_child_does_not_replace_base_skip_decorator_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = (
        "import pytest\n"
        "from ultimate_ai_agent.subject import DISABLED, runtime_value\n"
        "@pytest.mark.skipif(DISABLED, reason='unavailable')\n"
        "def test_case(): assert runtime_value() == 1\n"
    )
    _install_subject(
        tmp_path,
        monkeypatch,
        source,
        base_subject="DISABLED = False\ndef runtime_value(): return 1\n",
        current_subject=(
            "from ultimate_ai_agent.new_child import DISABLED, runtime_value\n"
        ),
        additions={CHILD_PATH: "DISABLED = True\ndef runtime_value(): return 1\n"},
    )

    removed = guard.removed_declarations(tmp_path, BASE_SHA)

    assert len(removed) == 1
    assert removed[0].startswith(TEST_PATH + "::test_case")


@pytest.mark.parametrize("autouse", [False, True], ids=["requested", "autouse"])
def test_new_application_fixture_cannot_hide_parameter_shrink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, autouse: bool
) -> None:
    test_source = "from ultimate_ai_agent.subject import fixture_value\n" + (
        "def test_case(): assert True\n"
        if autouse
        else "def test_case(fixture_value): assert fixture_value\n"
    )
    suffix = ", autouse=True" if autouse else ""
    base_subject = (
        "import pytest\n"
        f"@pytest.fixture(params=(1, 2){suffix})\n"
        "def fixture_value(request): return request.param\n"
    )
    child = (
        "import pytest\n"
        f"@pytest.fixture(params=(1,){suffix})\n"
        "def fixture_value(request): return request.param\n"
    )
    _install_subject(
        tmp_path,
        monkeypatch,
        test_source,
        base_subject=base_subject,
        current_subject="from ultimate_ai_agent.new_child import fixture_value\n",
        additions={CHILD_PATH: child},
    )

    try:
        removed = guard.removed_declarations(tmp_path, BASE_SHA)
    except guard.TestCorpusGuardError:
        return
    assert len(removed) == 1
    assert removed[0].startswith(TEST_PATH + "::test_case")


def test_new_test_helper_is_not_admitted_as_application_dependency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_subject(
        tmp_path,
        monkeypatch,
        AUTOUSE_TEST,
        current_subject="from tests.runtime_helper import runtime_value\n",
        additions={
            "tests/__init__.py": "",
            "tests/runtime_helper.py": "def runtime_value(): return 1\n",
        },
    )

    removed = guard.removed_declarations(tmp_path, BASE_SHA)

    assert len(removed) == 1
    assert "::autouse-sha256:" in removed[0]


def test_unrelated_new_application_import_is_not_admitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = (
        "import pytest\n"
        "from ultimate_ai_agent.unrelated import runtime_value\n"
        "@pytest.fixture(autouse=True)\n"
        "def fixture_value(): runtime_value()\n"
        "def test_case(): assert True\n"
    )
    _install_subject(
        tmp_path,
        monkeypatch,
        source,
        current_subject="def runtime_value(): return 1\n",
        additions={
            "src/ultimate_ai_agent/unrelated.py": "def runtime_value(): return 1\n"
        },
    )

    removed = guard.removed_declarations(tmp_path, BASE_SHA)

    assert len(removed) == 1
    assert "::autouse-sha256:" in removed[0]


def test_runtime_lookup_is_frozen_before_base_inventory_and_excludes_unrelated_modules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    unrelated_path = "src/ultimate_ai_agent/unrelated.py"
    _install_subject(
        tmp_path,
        monkeypatch,
        AUTOUSE_TEST,
        additions={
            CHILD_PATH: "def runtime_value(): return 1\n",
            unrelated_path: "def runtime_value(): return 2\n",
        },
    )
    original = guard._parse_base_test_declarations
    observations: dict[str, bool] = {}

    def inspect_resolver(*args, **kwargs):
        resolver = kwargs["python_runtime_import_source_resolver"]
        observations["child_prebound"] = (
            resolver("ultimate_ai_agent.new_child") is not None
        )
        observations["unrelated_initially_absent"] = (
            resolver("ultimate_ai_agent.unrelated") is None
        )
        declarations = original(*args, **kwargs)
        observations["child_admitted"] = (
            resolver("ultimate_ai_agent.new_child") is not None
        )
        observations["unrelated_still_absent"] = (
            resolver("ultimate_ai_agent.unrelated") is None
        )
        return declarations

    monkeypatch.setattr(guard, "_parse_base_test_declarations", inspect_resolver)

    assert guard.removed_declarations(tmp_path, BASE_SHA) == ()
    assert observations == {
        "child_prebound": True,
        "unrelated_initially_absent": True,
        "child_admitted": True,
        "unrelated_still_absent": True,
    }


def test_unresolved_runtime_dependency_remains_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_subject(
        tmp_path,
        monkeypatch,
        AUTOUSE_TEST,
        additions={
            CHILD_PATH: (
                "try:\n"
                "    import ultimate_ai_agent.absent_extension\n"
                "except ImportError:\n"
                "    pass\n"
                "def runtime_value(): return 1\n"
            ),
        },
    )
    original = guard._parse_base_test_declarations
    observations: list[bool] = []

    def inspect_resolver(*args, **kwargs):
        declarations = original(*args, **kwargs)
        resolver = kwargs["python_runtime_import_source_resolver"]
        observations.append(resolver("ultimate_ai_agent.absent_extension") is None)
        return declarations

    monkeypatch.setattr(guard, "_parse_base_test_declarations", inspect_resolver)

    assert guard.removed_declarations(tmp_path, BASE_SHA) == ()
    assert observations == [True]
    assert not (tmp_path / "src/ultimate_ai_agent/absent_extension.py").exists()


@pytest.mark.parametrize("mutation", ["replace", "remove", "shadow"])
def test_new_runtime_source_is_revalidated_after_base_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    _install_subject(tmp_path, monkeypatch, AUTOUSE_TEST)
    original = guard._parse_base_test_declarations

    def mutate_after_inventory(*args, **kwargs):
        declarations = original(*args, **kwargs)
        if mutation == "replace":
            (tmp_path / CHILD_PATH).write_text("def runtime_value(): return 2\n")
        elif mutation == "remove":
            (tmp_path / CHILD_PATH).unlink()
        else:
            _write_sources(
                tmp_path,
                {
                    "src/ultimate_ai_agent/new_child/__init__.py": (
                        "def runtime_value(): return 2\n"
                    )
                },
            )
        return declarations

    monkeypatch.setattr(guard, "_parse_base_test_declarations", mutate_after_inventory)

    with pytest.raises(guard.TestCorpusGuardError):
        guard.removed_declarations(tmp_path, BASE_SHA)


def test_missing_runtime_dependency_is_revalidated_after_base_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_subject(
        tmp_path,
        monkeypatch,
        AUTOUSE_TEST,
        additions={
            CHILD_PATH: (
                "try:\n"
                "    import ultimate_ai_agent.absent_extension\n"
                "except ImportError:\n"
                "    pass\n"
                "def runtime_value(): return 1\n"
            )
        },
    )
    original = guard._parse_base_test_declarations

    def mutate_after_inventory(*args, **kwargs):
        declarations = original(*args, **kwargs)
        _write_sources(
            tmp_path,
            {"src/ultimate_ai_agent/absent_extension.py": "VALUE = 1\n"},
        )
        return declarations

    monkeypatch.setattr(guard, "_parse_base_test_declarations", mutate_after_inventory)

    with pytest.raises(guard.TestCorpusGuardError):
        guard.removed_declarations(tmp_path, BASE_SHA)


@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
@pytest.mark.parametrize("target_kind", ["test", "test-helper"])
@pytest.mark.parametrize("mutation", ["replace", "remove"])
def test_preloaded_current_test_and_test_dependency_are_revalidated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    snapshot: bool,
    target_kind: str,
    mutation: str,
) -> None:
    helper_path = "tests/runtime_helper.py"
    source = AUTOUSE_TEST
    base_additions: dict[str, str] = {}
    if target_kind == "test-helper":
        source = (
            "import pytest\n"
            "from tests.runtime_helper import runtime_value\n"
            "@pytest.fixture(autouse=True)\n"
            "def fixture_value(): assert runtime_value() == 1\n"
            "def test_case(): assert True\n"
        )
        base_additions = {
            "tests/__init__.py": "",
            helper_path: "def runtime_value(): return 1\n",
        }
    _install_subject(tmp_path, monkeypatch, source, base_additions=base_additions)
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    original = guard._parse_base_test_declarations
    changed = False

    def mutate_after_inventory(*args, **kwargs):
        nonlocal changed
        declarations = original(*args, **kwargs)
        target = tmp_path / (TEST_PATH if target_kind == "test" else helper_path)
        if mutation == "remove":
            target.unlink()
        else:
            target.write_text(
                "def test_case(): assert False\n"
                if target_kind == "test"
                else "def runtime_value(): return 2\n"
            )
        changed = True
        return declarations

    monkeypatch.setattr(guard, "_parse_base_test_declarations", mutate_after_inventory)

    with pytest.raises(guard.TestCorpusGuardError):
        guard.removed_declarations(tmp_path, BASE_SHA, worktree_snapshot=inventory)
    assert changed


RETAINED_UNITTEST_SKIP_HELPER = (
    "import unittest\n"
    "import pytest\n"
    "from ultimate_ai_agent.subject import runtime_value\n"
    "def require_value(case):\n"
    "    value = runtime_value(case)\n"
    "    if value is None: pytest.skip('unavailable')\n"
    "    return value\n"
    "class TestCase(unittest.TestCase):\n"
    "    def test_retained(self):\n"
    "        assert require_value(self) == 1\n"
)


def _install_retained_unittest_method_subject(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    child_source: str,
    nested: bool,
) -> None:
    additions = {CHILD_PATH: child_source}
    if nested:
        additions = {
            CHILD_PATH: (
                "from ultimate_ai_agent.new_grandchild import runtime_value\n"
            ),
            GRANDCHILD_PATH: child_source,
        }
    _install_subject(
        tmp_path,
        monkeypatch,
        RETAINED_UNITTEST_SKIP_HELPER,
        base_subject="def runtime_value(case): return 1\n",
        additions=additions,
    )


@pytest.mark.parametrize(
    "child_source",
    [
        "def runtime_value(case): case.skipTest('unavailable')\n",
        (
            "def runtime_value(case):\n"
            "    abort = case.skipTest\n"
            "    abort('unavailable')\n"
        ),
        (
            "def runtime_value(case):\n"
            "    getattr(case, 'skipTest')('unavailable')\n"
        ),
        (
            "def runtime_value(case):\n"
            "    abort = getattr(case, 'skipTest', None)\n"
            "    abort('unavailable')\n"
        ),
        (
            "import builtins as builtin\n"
            "def runtime_value(case):\n"
            "    builtin.getattr(case, 'skipTest')('unavailable')\n"
        ),
        (
            "from builtins import getattr as lookup\n"
            "def runtime_value(case):\n"
            "    lookup(case, 'skipTest')('unavailable')\n"
        ),
        (
            "def runtime_value(case):\n"
            "    lookup = getattr\n"
            "    lookup(case, 'skipTest')('unavailable')\n"
        ),
        (
            "import builtins as builtin\n"
            "def runtime_value(case):\n"
            "    lookup = builtin.getattr\n"
            "    lookup(case, 'skipTest')('unavailable')\n"
        ),
        (
            "from builtins import getattr as imported_lookup\n"
            "def runtime_value(case):\n"
            "    lookup = imported_lookup\n"
            "    lookup(case, 'skipTest')('unavailable')\n"
        ),
        (
            "def bind_last():\n"
            "    global last\n"
            "    last = middle\n"
            "def bind_middle():\n"
            "    global middle\n"
            "    middle = first\n"
            "def bind_first():\n"
            "    global first\n"
            "    first = getattr\n"
            "def runtime_value(case):\n"
            "    bind_first()\n"
            "    bind_middle()\n"
            "    bind_last()\n"
            "    last(case, 'skipTest')('unavailable')\n"
        ),
        (
            "def runtime_value(case):\n"
            "    first = getattr\n"
            "    second = first\n"
            "    first = second\n"
            "    second(case, 'skipTest')('unavailable')\n"
        ),
        (
            "def runtime_value(case):\n"
            "    abort = lambda: case.skipTest('unavailable')\n"
            "    abort()\n"
        ),
        (
            "def runtime_value(case):\n"
            "    methods = [case.skipTest]\n"
            "    methods[0]('unavailable')\n"
        ),
        (
            "def dormant():\n"
            "    lookup = object\n"
            "    return lookup\n"
            "def runtime_value(case):\n"
            "    lookup = getattr\n"
            "    lookup(case, 'skipTest')('unavailable')\n"
        ),
        (
            "def runtime_value(case):\n"
            "    lookup = getattr\n"
            "    lookup(case, 'skipTest')('unavailable')\n"
            "def dormant():\n"
            "    lookup = object\n"
            "    return lookup\n"
        ),
    ],
    ids=[
        "direct-method",
        "captured-method",
        "literal-getattr",
        "captured-getattr-method",
        "builtins-getattr",
        "imported-getter",
        "assigned-getter",
        "assigned-builtins-getter",
        "assigned-imported-getter",
        "reversed-getter-chain",
        "seeded-getter-cycle",
        "lambda-method",
        "container-method",
        "conflicting-dormant-before",
        "conflicting-dormant-after",
    ],
)
@pytest.mark.parametrize("nested", [False, True], ids=["child", "grandchild"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_new_runtime_closure_cannot_hide_unittest_skip_method(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    child_source: str,
    nested: bool,
    snapshot: bool,
) -> None:
    # The unchanged helper already has a recognized skip branch, so its runtime
    # identity remains evidence. A direct test alone normalizes this helper away
    # in both old and new guards and would not prove this admission regression.
    _install_retained_unittest_method_subject(
        tmp_path, monkeypatch, child_source, nested
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None

    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )

    assert len(removed) == 1
    assert removed[0].startswith(f"{TEST_PATH}::TestCase::test_retained")


@pytest.mark.parametrize(
    "child_source",
    [
        "def runtime_value(case): return 1\n",
        "def runtime_value(case): return getattr(case, 'value', 1)\n",
        (
            "def runtime_value(case):\n"
            "    first = case\n"
            "    second = first\n"
            "    first = second\n"
            "    return 1\n"
        ),
        (
            "def runtime_value(case):\n"
            "    first = getattr\n"
            "    second = first\n"
            "    first = second\n"
            "    return second(case, 'value', 1)\n"
        ),
    ],
    ids=["plain", "harmless-getter", "non-getter-cycle", "harmless-getter-cycle"],
)
@pytest.mark.parametrize("nested", [False, True], ids=["child", "grandchild"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_new_runtime_closure_keeps_harmless_getter_and_alias_cycles(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    child_source: str,
    nested: bool,
    snapshot: bool,
) -> None:
    _install_retained_unittest_method_subject(
        tmp_path, monkeypatch, child_source, nested
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None

    assert (
        guard.removed_declarations(tmp_path, BASE_SHA, worktree_snapshot=inventory)
        == ()
    )


@pytest.mark.parametrize(
    "child_source",
    [
        "def runtime_value(case): getattr(case, 'skip' + 'Test')('unavailable')\n",
        "def runtime_value(case): getattr(case, ('s' + 'kip') + ('T' + 'est'))('unavailable')\n",
        "def runtime_value(case): getattr(case, 'skip' + 'Test', None)('unavailable')\n",
        "def runtime_value(case):\n    name = 'skipTest'\n    getattr(case, name)('unavailable')\n",
        'def runtime_value(case): getattr(case, f"{\'skip\'}Test")("unavailable")\n',
        "def runtime_value(case): getattr(case, ''.join(('skip', 'Test')))('unavailable')\n",
        "def runtime_value(case, name='skipTest'): getattr(case, name)('unavailable')\n",
        "def runtime_value(case): getattr(*(case, 'skipTest'))('unavailable')\n",
        "def runtime_value(case): getattr(case, name='skipTest')('unavailable')\n",
        "def runtime_value(case): getattr(case)\n",
        "def runtime_value(case): getattr(case, 'value', None, None)\n",
        "def runtime_value(case): getattr(case, 1)\n",
        "import builtins as builtin\ndef runtime_value(case): builtin.getattr(case, 'skip' + 'Test')('unavailable')\n",
        "from builtins import getattr as lookup\ndef runtime_value(case): lookup(case, 'skip' + 'Test')('unavailable')\n",
        "def runtime_value(case):\n    lookup = getattr\n    lookup(case, 'skip' + 'Test')('unavailable')\n",
        (
            "def bind_last():\n    global last\n    last = middle\n"
            "def bind_middle():\n    global middle\n    middle = first\n"
            "def bind_first():\n    global first\n    first = getattr\n"
            "def runtime_value(case):\n"
            "    bind_first()\n    bind_middle()\n    bind_last()\n"
            "    last(case, 'skip' + 'Test')('unavailable')\n"
        ),
        (
            "def runtime_value(case):\n    first = getattr\n"
            "    second = first\n    first = second\n"
            "    second(case, 'skip' + 'Test')('unavailable')\n"
        ),
        (
            "def dormant():\n    lookup = object\n    return lookup\n"
            "def runtime_value(case):\n    lookup = getattr\n"
            "    lookup(case, 'skip' + 'Test')('unavailable')\n"
        ),
        (
            "def runtime_value(case):\n    lookup = getattr\n"
            "    lookup(case, 'skip' + 'Test')('unavailable')\n"
            "def dormant():\n    lookup = object\n    return lookup\n"
        ),
        (
            "def runtime_value(case):\n"
            "    abort = getattr(case, 'skip' + 'Test')\n"
            "    abort('unavailable')\n"
        ),
        (
            "from builtins import getattr as lookup\n"
            "def runtime_value(case, name='skipTest'):\n"
            "    lookup(case, name)('unavailable')\n"
        ),
        (
            "def runtime_value(case):\n"
            "    abort = lambda: getattr(case, 'skip' + 'Test')('unavailable')\n"
            "    abort()\n"
        ),
        (
            "def runtime_value(case):\n"
            "    methods = [getattr(case, 'skip' + 'Test')]\n"
            "    methods[0]('unavailable')\n"
        ),
    ],
    ids=[
        "concat", "nested-concat", "concat-default", "bound-name", "f-string",
        "join", "caller-name", "starred-args", "keyword-selector",
        "missing-selector", "extra-argument", "non-string", "builtins-concat",
        "imported-concat", "assigned-concat", "reversed-chain-concat",
        "seeded-cycle-concat", "dormant-before-concat", "dormant-after-concat",
        "captured-concat", "imported-unknown", "lambda-concat", "container-concat",
    ],
)
@pytest.mark.parametrize("nested", [False, True], ids=["child", "grandchild"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_strict_runtime_getter_selection_cannot_erase_retained_test(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    child_source: str,
    nested: bool,
    snapshot: bool,
) -> None:
    _install_retained_unittest_method_subject(
        tmp_path, monkeypatch, child_source, nested
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None

    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )

    assert len(removed) == 1
    assert removed[0].startswith(f"{TEST_PATH}::TestCase::test_retained")


@pytest.mark.parametrize(
    "child_source",
    [
        "def runtime_value(case):\n    getattr(case, '__class__')\n    return 1\n",
        "def runtime_value(case): return getattr(case, 'val' + 'ue', 1)\n",
        "def runtime_value(case): return getattr(case, ('v' + 'al') + ('u' + 'e'), 1)\n",
        "from builtins import getattr as lookup\ndef runtime_value(case): return lookup(case, 'val' + 'ue', 1)\n",
        (
            "def runtime_value(case):\n    first = getattr\n"
            "    second = first\n    first = second\n"
            "    return second(case, 'val' + 'ue', 1)\n"
        ),
        (
            "def lookup(case, name): return 1\n"
            "def runtime_value(case, name='value'): return lookup(case, name)\n"
        ),
    ],
    ids=[
        "literal-two-args", "concat-default", "nested-default",
        "imported-concat", "seeded-cycle", "ordinary-callable",
    ],
)
@pytest.mark.parametrize("nested", [False, True], ids=["child", "grandchild"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_strict_runtime_getter_selection_preserves_proven_harmless_members(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    child_source: str,
    nested: bool,
    snapshot: bool,
) -> None:
    _install_retained_unittest_method_subject(
        tmp_path, monkeypatch, child_source, nested
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None

    assert guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    ) == ()


def _graph_source(*dependencies: str) -> str:
    # Distinct bindings make every intended edge visible to the existing
    # import grammar instead of shadowing the common package binding.
    return "".join(
        f"import {module} as dependency_{index}\n"
        for index, module in enumerate(dependencies)
    ) + (
        "def runtime_value(): return 1\n"
    )


def _graph_path(module: str) -> str:
    return "src/" + module.replace(".", "/") + ".py"


def _admit_source_graph(
    base: dict[str, str],
    current: dict[str, str],
    observed: tuple[str, ...],
    *,
    warm_current: tuple[str, ...] = (),
) -> dict[str, str]:
    # The canonical entrypoint also bounds the entire baseline module index.
    # Query its existing admission boundary directly for per-root budget cases
    # whose independent, individually valid closures have a larger union.
    base_paths = {PACKAGE_PATH: "", **{_graph_path(m): s for m, s in base.items()}}
    current_paths = {
        PACKAGE_PATH: "",
        **{_graph_path(m): s for m, s in current.items()},
    }
    worktree = guard._python_import_resolver(current_paths.get)
    baseline = guard._python_import_resolver(base_paths.get)
    proof = guard._python_import_resolver(current_paths.get)
    for module in observed:
        worktree(module)
    for module in warm_current:
        source = proof(module)
        assert source is not None
        assert guard._python_import_closure_is_collection_neutral(
            module, source, proof
        )
    return guard._python_admitted_runtime_sources(
        worktree, baseline, proof, base_paths.get
    )


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("independent_root", [False, True])
def test_failed_root_cannot_promote_discovered_existing_descendant(
    reverse: bool, independent_root: bool
) -> None:
    root = "ultimate_ai_agent.proof_root"
    descendant = "ultimate_ai_agent.proof_existing_descendant"
    good = "ultimate_ai_agent.proof_good"
    safe = "ultimate_ai_agent.proof_new_safe"
    unsafe = "ultimate_ai_agent.proof_new_unsafe"
    base = {
        root: _graph_source(descendant),
        descendant: _graph_source(),
        good: _graph_source(),
    }
    current = {
        **base,
        root: _graph_source(descendant, unsafe),
        descendant: _graph_source(safe),
        good: _graph_source(safe),
        safe: _graph_source(),
        unsafe: "def runtime_value(case, name): return getattr(case, name)\n",
    }
    observed = (root, good) if independent_root else (root,)
    if reverse:
        base = dict(reversed(tuple(base.items())))
        current = dict(reversed(tuple(current.items())))
        observed = tuple(reversed(observed))

    admitted = _admit_source_graph(base, current, observed)

    assert admitted == ({_graph_path(safe): current[safe]} if independent_root else {})
    assert _graph_path(unsafe) not in admitted


@pytest.mark.parametrize("over_revision", ["neither", "base", "current"])
@pytest.mark.parametrize("cycle", [False, True], ids=["chain", "cycle"])
def test_runtime_graph_preserves_each_revision_exact_closure_budget(
    monkeypatch: pytest.MonkeyPatch, over_revision: str, cycle: bool
) -> None:
    # Four old modules + the new leaf + the package initializer exactly fit six.
    # The extra existing node pushes only the selected revision over the bound.
    modules = tuple(f"ultimate_ai_agent.budget_{i}" for i in range(4))
    extra = "ultimate_ai_agent.budget_extra"
    leaf = "ultimate_ai_agent.budget_new_leaf"
    base = {
        module: _graph_source(modules[index + 1])
        if index + 1 < len(modules)
        else _graph_source(modules[0]) if cycle else _graph_source()
        for index, module in enumerate(modules)
    }
    base[extra] = _graph_source()
    current = {**base, leaf: _graph_source()}
    current[modules[-1]] = _graph_source(
        *((modules[0],) if cycle else ()), leaf
    )
    if over_revision == "base":
        # Two extra baseline members are needed: baseline lacks the new leaf.
        second_extra = "ultimate_ai_agent.budget_second_extra"
        base[second_extra] = _graph_source()
        base[modules[-1]] = _graph_source(extra, second_extra)
    elif over_revision == "current":
        current[modules[-1]] = _graph_source(
            *((modules[0],) if cycle else ()), leaf, extra
        )
    monkeypatch.setattr(guard, "MAX_PYTHON_DEPENDENCY_MODULES", 6)

    admitted = _admit_source_graph(base, current, (modules[0],))

    assert admitted == (
        {_graph_path(leaf): current[leaf]} if over_revision == "neither" else {}
    )


@pytest.mark.parametrize("observe_tail", [False, True])
def test_cached_exact_limit_tail_does_not_qualify_over_limit_prefix(
    monkeypatch: pytest.MonkeyPatch, observe_tail: bool
) -> None:
    tail = tuple(f"ultimate_ai_agent.a_tail_{i}" for i in range(4))
    prefix = "ultimate_ai_agent.z_prefix"
    leaf = "ultimate_ai_agent.new_leaf"
    base = {
        module: _graph_source(tail[index + 1])
        if index + 1 < len(tail) else _graph_source()
        for index, module in enumerate(tail)
    }
    base[prefix] = _graph_source(tail[0])
    current = {**base, tail[-1]: _graph_source(leaf), leaf: _graph_source()}
    monkeypatch.setattr(guard, "MAX_PYTHON_DEPENDENCY_MODULES", 6)

    admitted = _admit_source_graph(
        base, current, (tail[0], prefix) if observe_tail else (prefix,),
        warm_current=(tail[0],),
    )

    assert admitted == ({_graph_path(leaf): current[leaf]} if observe_tail else {})


@pytest.mark.parametrize("reverse", [False, True])
def test_disjoint_valid_runtime_roots_are_not_limited_by_their_union(
    monkeypatch: pytest.MonkeyPatch, reverse: bool
) -> None:
    roots = tuple(f"ultimate_ai_agent.disjoint_{i}" for i in range(8))
    leaves = tuple(f"ultimate_ai_agent.new_disjoint_{i}" for i in range(8))
    base = {root: _graph_source() for root in roots}
    current = {
        **{root: _graph_source(leaf) for root, leaf in zip(roots, leaves, strict=True)},
        **{leaf: _graph_source() for leaf in leaves},
    }
    monkeypatch.setattr(guard, "MAX_PYTHON_DEPENDENCY_MODULES", 3)

    admitted = _admit_source_graph(
        base, current, tuple(reversed(roots)) if reverse else roots
    )

    assert admitted == {_graph_path(leaf): current[leaf] for leaf in leaves}


@pytest.mark.parametrize("reverse", [False, True])
def test_oversized_component_preserves_small_successful_root(
    monkeypatch: pytest.MonkeyPatch, reverse: bool
) -> None:
    small = "ultimate_ai_agent.a_small"
    large = "ultimate_ai_agent.b_large"
    alternate = "ultimate_ai_agent.c_alternate"
    shared = "ultimate_ai_agent.new_shared"
    chain = tuple(f"ultimate_ai_agent.oversized_{i}" for i in range(5))
    base = {small: _graph_source(), large: _graph_source(), alternate: _graph_source()}
    current = {
        **base,
        small: _graph_source(shared),
        large: _graph_source(shared, chain[0]),
        alternate: _graph_source(shared, chain[1]),
        shared: _graph_source(),
        **{
            module: _graph_source(chain[index + 1])
            if index + 1 < len(chain) else _graph_source()
            for index, module in enumerate(chain)
        },
    }
    roots = (small, large, alternate)
    monkeypatch.setattr(guard, "MAX_PYTHON_DEPENDENCY_MODULES", 4)

    admitted = _admit_source_graph(
        base, current, tuple(reversed(roots)) if reverse else roots
    )

    assert admitted == {_graph_path(shared): current[shared]}


@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
@pytest.mark.parametrize("mutation", ["initializer", "absent-module", "absent-package"])
def test_runtime_graph_revalidates_ancestor_and_negative_candidate_observations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, snapshot: bool, mutation: str
) -> None:
    _install_subject(
        tmp_path, monkeypatch, SKIP_HELPER_TEST,
        additions={CHILD_PATH: (
            "try:\n    import ultimate_ai_agent.absent_extension\n"
            "except ImportError:\n    pass\n"
            "def runtime_value(): return 1\n"
        )},
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    original = guard._parse_base_test_declarations
    changed = False

    def mutate_after_inventory(*args, **kwargs):
        nonlocal changed
        declarations = original(*args, **kwargs)
        path = {
            "initializer": PACKAGE_PATH,
            "absent-module": "src/ultimate_ai_agent/absent_extension.py",
            "absent-package": "src/ultimate_ai_agent/absent_extension/__init__.py",
        }[mutation]
        _write_sources(tmp_path, {path: "VALUE = 1\n"})
        changed = True
        return declarations

    monkeypatch.setattr(guard, "_parse_base_test_declarations", mutate_after_inventory)

    with pytest.raises(guard.TestCorpusGuardError):
        guard.removed_declarations(tmp_path, BASE_SHA, worktree_snapshot=inventory)
    assert changed


@pytest.mark.parametrize("reverse", [False, True])
def test_incomplete_large_root_preserves_independent_closed_shared_root(
    monkeypatch: pytest.MonkeyPatch, reverse: bool
) -> None:
    good = "ultimate_ai_agent.closed_good"
    bad = "ultimate_ai_agent.incomplete_bad"
    member = "ultimate_ai_agent.new_closed_member"
    leaf = "ultimate_ai_agent.new_closed_leaf"
    chain = tuple(f"ultimate_ai_agent.incomplete_{i}" for i in range(8))
    base = {good: _graph_source(), bad: _graph_source()}
    current = {
        good: _graph_source(member),
        bad: _graph_source(good, chain[0]),
        member: _graph_source(leaf),
        leaf: _graph_source(),
        **{
            module: _graph_source(chain[index + 1])
            if index + 1 < len(chain) else _graph_source()
            for index, module in enumerate(chain)
        },
    }
    monkeypatch.setattr(guard, "MAX_PYTHON_DEPENDENCY_MODULES", 4)

    admitted = _admit_source_graph(
        base, current, (bad, good) if reverse else (good, bad)
    )

    assert admitted == {_graph_path(m): current[m] for m in (member, leaf)}


@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_runtime_graph_revalidates_unchosen_leading_import_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, snapshot: bool
) -> None:
    package = "src/ultimate_ai_agent/value_package/__init__.py"
    _install_subject(
        tmp_path, monkeypatch, SKIP_HELPER_TEST,
        additions={
            CHILD_PATH: (
                "from ultimate_ai_agent.value_package import value\n"
                "def runtime_value(): return value\n"
            ),
            package: "value = 1\n",
        },
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    original = guard._parse_base_test_declarations

    def mutate_after_inventory(*args, **kwargs):
        declarations = original(*args, **kwargs)
        _write_sources(
            tmp_path,
            {"src/ultimate_ai_agent/value_package/value.py": "VALUE = 1\n"},
        )
        return declarations

    monkeypatch.setattr(guard, "_parse_base_test_declarations", mutate_after_inventory)

    with pytest.raises(guard.TestCorpusGuardError):
        guard.removed_declarations(tmp_path, BASE_SHA, worktree_snapshot=inventory)


def _observe_runtime_graph_work(monkeypatch: pytest.MonkeyPatch) -> dict:
    from collections import Counter

    counts = {
        "facts": Counter(),
        "edge_builds": Counter(),
        "constructed_edges": 0,
        "neighbor_calls": 0,
        "neighbor_edges": 0,
        "fallback_calls": 0,
        "fallback_neighbor_calls": 0,
        "fallback_neighbor_edges": 0,
        "collector_calls": 0,
    }
    phase = {"admission": False, "fallback": False}
    original_admit = guard._python_admitted_runtime_sources
    original_facts = guard._python_collection_node_facts
    original_edges = guard._python_collection_node_edges
    original_neighbors = guard._python_collection_graph_neighbors
    original_fallback = guard._python_exact_closure_budget
    original_closure = guard._python_import_closure_is_collection_neutral

    def admit(*args, **kwargs):
        phase["admission"] = True
        try:
            return original_admit(*args, **kwargs)
        finally:
            phase["admission"] = False

    def facts(module, source, resolver):
        if phase["admission"]:
            counts["facts"][(id(resolver), module, source)] += 1
        return original_facts(module, source, resolver)

    def edges(module, source, resolver):
        result = original_edges(module, source, resolver)
        if phase["admission"]:
            counts["edge_builds"][(id(resolver), module, source)] += 1
            counts["constructed_edges"] += len(result)
        return result

    def neighbors(edge_map, module):
        result = original_neighbors(edge_map, module)
        if phase["admission"]:
            prefix = "fallback_" if phase["fallback"] else ""
            counts[prefix + "neighbor_calls"] += 1
            counts[prefix + "neighbor_edges"] += len(result)
        return result

    def fallback(graph, root, limit):
        if phase["admission"]:
            counts["fallback_calls"] += 1
        prior = phase["fallback"]
        phase["fallback"] = True
        try:
            return original_fallback(graph, root, limit)
        finally:
            phase["fallback"] = prior

    def closure(*args, **kwargs):
        if phase["admission"] and kwargs.get("resolved_sources") is not None:
            counts["collector_calls"] += 1
        return original_closure(*args, **kwargs)

    monkeypatch.setattr(guard, "_python_admitted_runtime_sources", admit)
    monkeypatch.setattr(guard, "_python_collection_node_facts", facts)
    monkeypatch.setattr(guard, "_python_collection_node_edges", edges)
    monkeypatch.setattr(guard, "_python_collection_graph_neighbors", neighbors)
    monkeypatch.setattr(guard, "_python_exact_closure_budget", fallback)
    monkeypatch.setattr(guard, "_python_import_closure_is_collection_neutral", closure)
    return counts


def _shared_runtime_graph(shape: str, size: int, addition: str):
    modules = tuple(f"ultimate_ai_agent.linear_{i:03d}" for i in range(size))
    base = {}
    if shape == "diamond":
        roots = (modules[0],)
        for index, module in enumerate(modules):
            if index + 1 == size:
                base[module] = _graph_source()
            else:
                left = module + "_left"
                right = module + "_right"
                base[module] = _graph_source(left, right)
                base[left] = _graph_source(modules[index + 1])
                base[right] = _graph_source(modules[index + 1])
    elif shape == "independent":
        roots = modules
        base = {module: _graph_source() for module in modules}
    else:
        roots = (modules[0],)
        for index, module in enumerate(modules):
            dependencies = (
                (modules[index + 1],) if index + 1 < size
                else (modules[0],) if shape == "cycle" else ()
            )
            base[module] = _graph_source(*dependencies)
    current = dict(base)
    if addition != "none":
        child = "ultimate_ai_agent.new_child"
        grandchild = "ultimate_ai_agent.new_grandchild"
        for module in modules if shape == "independent" else (modules[-1],):
            current[module] = f"import {child}\n" + current[module]
        current[child] = _graph_source(grandchild) if addition == "grandchild" else _graph_source()
        if addition == "grandchild":
            current[grandchild] = _graph_source()
    return roots, base, current


@pytest.mark.parametrize("shape", ["chain", "diamond", "cycle", "independent"])
@pytest.mark.parametrize("addition", ["none", "leaf", "grandchild"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_canonical_runtime_graph_construction_has_linear_operation_growth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    addition: str,
    snapshot: bool,
) -> None:
    observations = []
    for size in (16, 32):
        with monkeypatch.context() as patch:
            roots, base, current = _shared_runtime_graph(shape, size, addition)
            folder = tmp_path / f"size_{size}"
            _install_subject(
                folder, patch, SKIP_HELPER_TEST,
                base_subject=_graph_source(*roots),
                current_subject=_graph_source(*roots),
                base_additions={_graph_path(m): s for m, s in base.items()},
                additions={_graph_path(m): s for m, s in current.items()},
            )
            counts = _observe_runtime_graph_work(patch)
            inventory = guard._inventory_worktree_snapshot(folder) if snapshot else None

            assert guard.removed_declarations(
                folder, BASE_SHA, worktree_snapshot=inventory
            ) == ()

            assert counts["facts"]
            assert max(counts["facts"].values()) == 1
            assert max(counts["edge_builds"].values()) == 1
            assert counts["collector_calls"] == 0
            assert counts["fallback_calls"] == 0
            assert counts["fallback_neighbor_calls"] == 0
            actual_nodes = len(counts["facts"])
            actual_edges = counts["constructed_edges"]
            ordinary_work = counts["neighbor_calls"] + counts["neighbor_edges"]
            assert ordinary_work <= 16 * (actual_nodes + actual_edges)
            observations.append(ordinary_work)

    # The exact counters, not execution time, distinguish a shared graph from
    # repeatedly walking every cached suffix when the graph doubles in size.
    assert observations[1] <= 2.3 * observations[0] + 16


def test_runtime_graph_budget_fallback_counts_real_work_separately(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    roots = tuple(f"ultimate_ai_agent.small_root_{i}" for i in range(8))
    leaves = tuple(f"ultimate_ai_agent.small_leaf_{i}" for i in range(8))
    base = {root: _graph_source() for root in roots}
    current = {
        **{root: _graph_source(leaf) for root, leaf in zip(roots, leaves, strict=True)},
        **{leaf: _graph_source() for leaf in leaves},
    }
    counts = _observe_runtime_graph_work(monkeypatch)
    monkeypatch.setattr(guard, "MAX_PYTHON_DEPENDENCY_MODULES", 3)

    admitted = _admit_source_graph(base, current, roots)

    assert admitted == {_graph_path(leaf): current[leaf] for leaf in leaves}
    assert counts["fallback_calls"] > 0
    assert counts["fallback_neighbor_calls"] > 0
    assert counts["fallback_neighbor_edges"] > 0
    assert counts["collector_calls"] == 0
    assert max(counts["facts"].values()) == 1
    assert max(counts["edge_builds"].values()) == 1
    assert counts["fallback_neighbor_calls"] <= 4 * counts["fallback_calls"]


@pytest.mark.parametrize("new_member_calls_old_helper", [False, True])
def test_runtime_graph_checks_old_execution_dependencies_only_when_new_member_reaches_them(
    new_member_calls_old_helper: bool,
) -> None:
    root = "ultimate_ai_agent.old_runtime_root"
    helper = "ultimate_ai_agent.old_reflective_helper"
    child = "ultimate_ai_agent.new_runtime_member"
    reflection = "def runtime_value(case, name): return getattr(case, name)\n"
    base = {root: reflection, helper: reflection}
    current = {
        **base,
        root: f"import {child}\n" + reflection,
        child: _graph_source(helper) if new_member_calls_old_helper else _graph_source(),
    }

    admitted = _admit_source_graph(base, current, (root,))

    assert admitted == (
        {} if new_member_calls_old_helper else {_graph_path(child): current[child]}
    )


@pytest.mark.parametrize("reverse", [False, True])
def test_preobserved_missing_module_does_not_become_an_eligible_root(
    reverse: bool,
) -> None:
    root = "ultimate_ai_agent.existing_observed_root"
    child = "ultimate_ai_agent.new_observed_child"
    missing = "ultimate_ai_agent.absent_observed_module"
    base = {root: _graph_source()}
    current = {root: _graph_source(child), child: _graph_source()}

    admitted = _admit_source_graph(
        base, current, (missing, root) if reverse else (root, missing)
    )

    assert admitted == {_graph_path(child): current[child]}


@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_rejected_root_still_revalidates_proof_only_missing_observation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, snapshot: bool
) -> None:
    _install_subject(
        tmp_path, monkeypatch, SKIP_HELPER_TEST,
        additions={CHILD_PATH: (
            "try:\n    import ultimate_ai_agent.absent_extension\n"
            "except ImportError:\n    pass\n"
            "def runtime_value(case, name): return getattr(case, name)\n"
        )},
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    original = guard._parse_base_test_declarations

    def mutate_after_inventory(*args, **kwargs):
        declarations = original(*args, **kwargs)
        _write_sources(
            tmp_path, {"src/ultimate_ai_agent/absent_extension.py": "VALUE = 1\n"}
        )
        return declarations

    monkeypatch.setattr(guard, "_parse_base_test_declarations", mutate_after_inventory)

    with pytest.raises(guard.TestCorpusGuardError):
        guard.removed_declarations(tmp_path, BASE_SHA, worktree_snapshot=inventory)


@pytest.mark.parametrize("backedge_first", [False, True])
@pytest.mark.parametrize(
    "exit_source",
    [
        "def runtime_value(case, name): return getattr(case, name)\n",
        (
            "import importlib\n"
            "def runtime_value(name): return importlib.import_module(name)\n"
        ),
        "import pytest\npytest.skip('unavailable', allow_module_level=True)\n",
        "def runtime_value(:\n",
    ],
    ids=["unsafe-getter", "unresolved-dynamic", "collection-abort", "malformed"],
)
def test_cycle_backedge_cannot_certify_before_bad_exit_is_processed(
    backedge_first: bool, exit_source: str
) -> None:
    root = "ultimate_ai_agent.old_cycle_root"
    first = "ultimate_ai_agent.new_cycle_first"
    second = "ultimate_ai_agent.new_cycle_second"
    exit_member = "ultimate_ai_agent.new_cycle_exit"
    exits = (first, exit_member) if backedge_first else (exit_member, first)
    base = {root: _graph_source()}
    current = {
        root: _graph_source(first),
        first: _graph_source(second),
        second: _graph_source(*exits),
        exit_member: exit_source,
    }

    assert _admit_source_graph(base, current, (root,)) == {}


@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
@pytest.mark.parametrize("shape", ["independent", "late-chain-roots"])
def test_whole_comparison_bounds_baseline_only_graph_materialization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, snapshot: bool, shape: str
) -> None:
    from collections import Counter

    observations = []
    for size in (8, 16, 32):
        with monkeypatch.context() as patch:
            modules = tuple(f"ultimate_ai_agent.old_subject_{i:03d}" for i in range(size))
            ordered = tuple(reversed(modules)) if shape == "late-chain-roots" else modules
            test_source = (
                "import pytest\n"
                + "".join(
                    f"from {module} import runtime_value as call_{index}\n"
                    for index, module in enumerate(ordered)
                )
                + "def require_value():\n"
                + "".join(
                    f"    if call_{index}() is None: pytest.skip('unavailable')\n"
                    for index in range(size)
                )
                + "    return 1\ndef test_case(): assert require_value() == 1\n"
            )
            sources = {
                _graph_path(module): _graph_source(modules[index + 1])
                if shape == "late-chain-roots" and index + 1 < size
                else _graph_source()
                for index, module in enumerate(modules)
            }
            folder = tmp_path / f"size_{size}"
            _install_subject(
                folder, patch, test_source,
                base_subject="VALUE = 1\n", current_subject="VALUE = 1\n",
                base_additions=sources, additions={},
            )
            (folder / TEST_PATH).write_text("def test_case(): assert True\n")
            facts = Counter()
            edge_builds = Counter()
            work = {"constructed_edges": 0, "neighbor_events": 0, "snapshot_entries": 0}
            snapshots = {}
            original_facts = guard._python_collection_node_facts
            original_edges = guard._python_collection_node_edges
            original_neighbors = guard._python_collection_graph_neighbors
            original_freeze = guard._PythonCollectionGraphBuilder.freeze

            def count_facts(module, source, resolver):
                facts[(id(resolver), module, source)] += 1
                return original_facts(module, source, resolver)

            def count_edges(module, source, resolver):
                result = original_edges(module, source, resolver)
                edge_builds[(id(resolver), module, source)] += 1
                work["constructed_edges"] += len(result or ())
                return result

            def count_neighbors(edges, module):
                result = original_neighbors(edges, module)
                work["neighbor_events"] += 1 + len(result)
                return result

            def count_materialization(builder):
                result = original_freeze(builder)
                if id(result) not in snapshots:
                    # Retain identity so object-ID reuse cannot hide emitted
                    # snapshots; count actual returned source records once.
                    snapshots[id(result)] = result
                    work["snapshot_entries"] += len(result.sources)
                return result

            patch.setattr(guard, "_python_collection_node_facts", count_facts)
            patch.setattr(guard, "_python_collection_node_edges", count_edges)
            patch.setattr(guard, "_python_collection_graph_neighbors", count_neighbors)
            patch.setattr(guard._PythonCollectionGraphBuilder, "freeze", count_materialization)
            inventory = guard._inventory_worktree_snapshot(folder) if snapshot else None

            removed = guard.removed_declarations(
                folder, BASE_SHA, worktree_snapshot=inventory
            )

            assert len(removed) == 1
            assert removed[0].startswith(f"{TEST_PATH}::test_case")
            assert facts
            assert max(facts.values()) == 1
            assert max(edge_builds.values()) == 1
            assert work["snapshot_entries"] <= 16 * len(facts)
            assert work["neighbor_events"] <= 16 * (
                len(facts) + work["constructed_edges"]
            )
            observations.append(work)

    for previous, current in zip(observations, observations[1:]):
        assert current["snapshot_entries"] <= 2.3 * previous["snapshot_entries"] + 16
        assert current["neighbor_events"] <= 2.3 * previous["neighbor_events"] + 16
