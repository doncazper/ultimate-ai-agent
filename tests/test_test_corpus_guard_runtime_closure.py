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

    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    if test_source == SKIP_HELPER_TEST:
        # An unchanged caller can skip when a changed application result differs.
        # Preserve strict identity; collection-neutrality cannot prove values.
        assert len(removed) == 1
        assert removed[0].startswith(f"{TEST_PATH}::test_case")
    else:
        assert removed == ()


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

    # Harmless new subjects remain admissible independently of this caller's
    # existing skip branch, whose dependency identity must stay revision-bound.
    _assert_harmless_runtime_subject_admitted(child_source, nested)
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    assert len(removed) == 1
    assert removed[0].startswith(f"{TEST_PATH}::TestCase::test_retained")


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

    # Harmless new subjects remain admissible independently of this caller's
    # existing skip branch, whose dependency identity must stay revision-bound.
    _assert_harmless_runtime_subject_admitted(child_source, nested)
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    assert len(removed) == 1
    assert removed[0].startswith(f"{TEST_PATH}::TestCase::test_retained")


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


_GETTER_CALL_WRAPPERS = (
    ("namedexpr", "(lookup := getattr)"),
    ("nested-namedexpr", "(outer := (inner := getattr))"),
    ("conditional", "(getattr if case else getattr)"),
    ("boolean", "(None or getattr)"),
    ("tuple-member", "(getattr,)[0]"),
    ("list-member", "[getattr][0]"),
    ("mapping-member", "{'lookup': getattr}['lookup']"),
    ("returned-getter", "(lambda: getattr)()"),
    ("passed-getter", "(lambda lookup: lookup)(getattr)"),
)


def _wrapped_getter_source(wrapper: str, *, safe: bool = False) -> str:
    if safe:
        return f"def runtime_value(case): return {wrapper}(case, 'value', 1)\n"
    return (
        f"def runtime_value(case): {wrapper}(case, 'skip' + 'Test')('unavailable')\n"
    )


@pytest.mark.parametrize("_label,wrapper", _GETTER_CALL_WRAPPERS)
@pytest.mark.parametrize("nested", [False, True], ids=["child", "grandchild"])
def test_getter_callable_wrapper_is_refused_at_frozen_admission(
    _label: str, wrapper: str, nested: bool
) -> None:
    base = {"ultimate_ai_agent.subject": "def runtime_value(case): return 1\n"}
    current = {
        "ultimate_ai_agent.subject": "from ultimate_ai_agent.new_child import runtime_value\n",
        "ultimate_ai_agent.new_child": _wrapped_getter_source(wrapper),
    }
    if nested:
        current["ultimate_ai_agent.new_grandchild"] = current["ultimate_ai_agent.new_child"]
        current["ultimate_ai_agent.new_child"] = (
            "from ultimate_ai_agent.new_grandchild import runtime_value\n"
        )

    # Real resolvers and the frozen admission transaction isolate this screen
    # from the separate strict identity of an abort-capable test consumer.
    assert _admit_source_graph(base, current, ("ultimate_ai_agent.subject",)) == {}


@pytest.mark.parametrize("_label,wrapper", _GETTER_CALL_WRAPPERS)
@pytest.mark.parametrize("nested", [False, True], ids=["child", "grandchild"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_getter_callable_wrapper_cannot_erase_retained_assertion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    _label: str, wrapper: str, nested: bool, snapshot: bool,
) -> None:
    _install_retained_unittest_method_subject(
        tmp_path, monkeypatch, _wrapped_getter_source(wrapper), nested
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
        _wrapped_getter_source("(lookup := getattr)", safe=True),
        _wrapped_getter_source("(outer := (inner := getattr))", safe=True),
        "def runtime_value(case): return (lookup := lambda obj, name, default: default)(case, 'skipTest', 1)\n",
        "def runtime_value(case): return (lambda: 1)()\n",
    ],
    ids=["safe-namedexpr", "safe-nested-namedexpr", "non-getter", "ordinary-lambda"],
)
@pytest.mark.parametrize("nested", [False, True], ids=["child", "grandchild"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_safe_callable_wrappers_preserve_abort_free_consumer_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    child_source: str, nested: bool, snapshot: bool,
) -> None:
    test_source = (
        "from ultimate_ai_agent.subject import runtime_value\n"
        "def test_case(): assert runtime_value(object()) == 1\n"
    )
    additions = {CHILD_PATH: child_source}
    if nested:
        additions = {
            CHILD_PATH: "from ultimate_ai_agent.new_grandchild import runtime_value\n",
            GRANDCHILD_PATH: child_source,
        }
    _install_subject(
        tmp_path, monkeypatch, test_source,
        base_subject="def runtime_value(case): return 1\n", additions=additions,
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    _assert_harmless_runtime_subject_admitted(child_source, nested)

    assert guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    ) == ()


_CALLER_ABORT_FORMS = (
    "direct", "helper", "helper-chain", "autouse", "requested-fixture",
    "imported-helper", "module-object", "callback", "xfail", "exception",
    "imported-receiver", "local-receiver", "callback-owned-abort", "requested-value",
    "abort-capability", "imported-abort-capability",
    "reexported-abort-capability", "class-helper",
    "requested-fixture-chain", "autouse-fixture-chain",
)


def _caller_abort_subject(form: str) -> tuple[str, dict[str, str]]:
    imports = "import pytest\nfrom ultimate_ai_agent.subject import runtime_value\n"
    check = "    if value is None: pytest.skip('unavailable')\n"
    helper = "def require_value():\n    value = runtime_value()\n" + check + "    return value\n"
    if form in {"requested-fixture-chain", "autouse-fixture-chain"}:
        outer = (
            "@pytest.fixture(autouse=True)\ndef outer(require_value): return 1\n"
            if form == "autouse-fixture-chain" else
            "@pytest.fixture\ndef outer(require_value): return 1\n"
        )
        test = (
            "def test_case(): assert True\n"
            if form == "autouse-fixture-chain" else
            "def test_case(outer): assert outer == 1\n"
        )
        return imports + "@pytest.fixture\n" + helper + outer + test, {}
    if form == "class-helper":
        return imports + (
            "class TestCase:\n"
            "    def require_value(self):\n        value = runtime_value()\n"
            "        if value is None: pytest.skip('unavailable')\n"
            "        return value\n"
            "    def test_case(self): assert self.require_value() == 1\n"
        ), {}
    if form == "reexported-abort-capability":
        return imports + (
            "from tests.helpers import abort\n"
            "def test_case(): assert runtime_value(abort) == 1\n"
        ), {"tests/__init__.py": "", "tests/helpers.py": "from pytest import skip as abort\n"}
    if form == "abort-capability":
        return imports + "def test_case(): assert runtime_value(pytest.skip) == 1\n", {}
    if form == "imported-abort-capability":
        return imports + (
            "from tests.helpers import abort\n"
            "def test_case(): assert runtime_value(abort) == 1\n"
        ), {"tests/__init__.py": "", "tests/helpers.py": "import pytest\ndef abort(reason): pytest.skip(reason)\n"}
    if form == "imported-receiver":
        return (
            "import ultimate_ai_agent.subject as subject\n"
            "from tests.helpers import require_value\n"
            "def test_case(): assert require_value(subject.runtime_value()) == 1\n",
            {"tests/__init__.py": "", "tests/helpers.py": "import pytest\ndef require_value(value):\n" + check + "    return value\n"},
        )
    if form == "local-receiver":
        return imports + "def require_value(value):\n" + check + (
            "    return value\ndef test_case(): assert require_value(runtime_value()) == 1\n"
        ), {}
    if form == "callback-owned-abort":
        return imports + (
            "def runner(callback): return callback(runtime_value())\n"
            "def test_case():\n    def check(value):\n"
            "        if value is None: pytest.skip('unavailable')\n"
            "        return value\n    assert runner(check) == 1\n"
        ), {}
    if form == "requested-value":
        return imports + (
            "@pytest.fixture\ndef value(): return runtime_value()\n"
            "def test_case(value):\n" + check + "    assert value == 1\n"
        ), {}
    if form == "direct":
        return imports + "def test_case():\n    value = runtime_value()\n" + check + "    assert value == 1\n", {}
    if form == "helper":
        return SKIP_HELPER_TEST, {}
    if form == "helper-chain":
        return imports + helper + "def outer(): return require_value()\ndef test_case(): assert outer() == 1\n", {}
    if form in {"autouse", "requested-fixture"}:
        decorator = "@pytest.fixture(autouse=True)\n" if form == "autouse" else "@pytest.fixture\n"
        test = "def test_case(): assert True\n" if form == "autouse" else "def test_case(require_value): assert require_value == 1\n"
        return imports + decorator + helper + test, {}
    if form == "imported-helper":
        return (
            "from tests.helpers import require_value\ndef test_case(): assert require_value() == 1\n",
            {"tests/__init__.py": "", "tests/helpers.py": imports + helper},
        )
    if form == "module-object":
        return (
            "import pytest\nimport ultimate_ai_agent.subject as subject\n"
            "def test_case():\n    value = subject.runtime_value()\n" + check + "    assert value == 1\n"
        ), {}
    if form == "callback":
        return imports + (
            "def require_value(callback):\n    value = callback()\n" + check
            + "    return value\ndef test_case(): assert require_value(runtime_value) == 1\n"
        ), {}
    if form == "xfail":
        return imports + (
            "def test_case():\n    value = runtime_value()\n"
            "    if value is None: pytest.xfail('unavailable')\n    assert value == 1\n"
        ), {}
    assert form == "exception"
    return imports + (
        "def test_case():\n    try:\n        value = runtime_value()\n"
        "    except ValueError:\n        pytest.skip('unavailable')\n    assert value == 1\n"
    ), {}


@pytest.mark.parametrize("form", _CALLER_ABORT_FORMS)
@pytest.mark.parametrize("topology", ["existing-app", "child", "grandchild"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_caller_owned_abort_retains_revision_specific_application_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    form: str, topology: str, snapshot: bool,
) -> None:
    test_source, support = _caller_abort_subject(form)
    base_subject = (
        "def runtime_value(callback): return 1\n"
        if form.endswith("abort-capability") else "def runtime_value(): return 1\n"
    )
    changed = (
        "def runtime_value(callback): callback('unavailable')\n"
        if form.endswith("abort-capability") else
        "def runtime_value(): raise ValueError('unavailable')\n"
        if form == "exception" else "def runtime_value(): return None\n"
    )
    current_subject = "from ultimate_ai_agent.new_child import runtime_value\n"
    additions = {CHILD_PATH: changed}
    if topology == "existing-app":
        current_subject, additions = changed, {}
    elif topology == "grandchild":
        additions = {
            CHILD_PATH: "from ultimate_ai_agent.new_grandchild import runtime_value\n",
            GRANDCHILD_PATH: changed,
        }
    _install_subject(
        tmp_path, monkeypatch, test_source, current_subject=current_subject,
        base_subject=base_subject, base_additions=support, additions=additions,
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None

    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )

    assert len(removed) == 1
    expected = "TestCase::test_case" if form == "class-helper" else "test_case"
    assert removed[0].startswith(f"{TEST_PATH}::{expected}")


@pytest.mark.parametrize("returned", ["None", "False", "2"])
@pytest.mark.parametrize("topology", ["existing-app", "child"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_application_result_change_keeps_ordinary_assertion_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    returned: str, topology: str, snapshot: bool,
) -> None:
    changed = f"def runtime_value(): return {returned}\n"
    options = (
        {"current_subject": changed, "additions": {}}
        if topology == "existing-app" else {"additions": {CHILD_PATH: changed}}
    )
    _install_subject(tmp_path, monkeypatch, DIRECT_TEST, **options)
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None

    assert guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    ) == ()


@pytest.mark.parametrize("form", _CALLER_ABORT_FORMS)
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_unchanged_abort_sensitive_application_identity_is_stable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, form: str, snapshot: bool,
) -> None:
    test_source, support = _caller_abort_subject(form)
    unchanged = (
        "def runtime_value(callback): return 1\n"
        if form.endswith("abort-capability") else "def runtime_value(): return 1\n"
    )
    _install_subject(
        tmp_path, monkeypatch, test_source,
        base_subject=unchanged, current_subject=unchanged, additions={},
        base_additions=support,
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None

    assert guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    ) == ()


@pytest.mark.parametrize("sensitive_first", [False, True])
@pytest.mark.parametrize("topology", ["existing-app", "child"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_shared_application_normalization_is_consumer_local_and_order_independent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    sensitive_first: bool, topology: str, snapshot: bool,
) -> None:
    imports = "import pytest\nfrom ultimate_ai_agent.subject import runtime_value\n"
    sensitive = (
        "def test_sensitive():\n    value = runtime_value()\n"
        "    if value is None: pytest.skip('unavailable')\n    assert value == 1\n"
    )
    ordinary = "def test_ordinary(): assert runtime_value() == 1\n"
    test_source = imports + (sensitive + ordinary if sensitive_first else ordinary + sensitive)
    changed = "def runtime_value(): return None\n"
    options = (
        {"current_subject": changed, "additions": {}}
        if topology == "existing-app" else {"additions": {CHILD_PATH: changed}}
    )
    _install_subject(tmp_path, monkeypatch, test_source, **options)
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None

    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )

    assert len(removed) == 1
    assert removed[0].startswith(f"{TEST_PATH}::test_sensitive")



def _assert_harmless_runtime_subject_admitted(child_source: str, nested: bool) -> None:
    base = {"ultimate_ai_agent.subject": "def runtime_value(case): return 1\n"}
    current = {
        "ultimate_ai_agent.subject": "from ultimate_ai_agent.new_child import runtime_value\n",
        "ultimate_ai_agent.new_child": child_source,
    }
    expected = {CHILD_PATH}
    if nested:
        current["ultimate_ai_agent.new_grandchild"] = child_source
        current["ultimate_ai_agent.new_child"] = (
            "from ultimate_ai_agent.new_grandchild import runtime_value\n"
        )
        expected.add(GRANDCHILD_PATH)
    admitted = _admit_source_graph(base, current, ("ultimate_ai_agent.subject",))
    assert set(admitted) == expected
    assert admitted[GRANDCHILD_PATH if nested else CHILD_PATH] == child_source


@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_sensitive_consumer_identity_ignores_unrelated_source_locations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, snapshot: bool,
) -> None:
    _install_subject(
        tmp_path, monkeypatch, SKIP_HELPER_TEST,
        current_subject="def runtime_value(): return 1\n", additions={},
    )
    (tmp_path / TEST_PATH).write_text(
        "\n\ndef test_unrelated(): assert True\n\n" + SKIP_HELPER_TEST,
        encoding="utf-8",
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None

    assert guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    ) == ()


@pytest.mark.parametrize(
    "source,unsafe",
    [
        (
            "import builtins\ndef runtime_value(case): (namespace := builtins).getattr(case, 'skip' + 'Test')('unavailable')\n",
            True,
        ),
        (
            "import builtins\nnamespace = builtins\ndef runtime_value(case): namespace.getattr(case, 'skip' + 'Test')('unavailable')\n",
            True,
        ),
        (
            "import builtins\ndef runtime_value(case):\n    namespace = builtins\n    namespace.getattr(case, 'skip' + 'Test')('unavailable')\n",
            True,
        ),
        ("import builtins\ndef runtime_value(case): return builtins.len((1,))\n", False),
    ],
    ids=["inline-namespace", "module-namespace", "local-namespace", "ordinary-builtin"],
)
@pytest.mark.parametrize("nested", [False, True], ids=["child", "grandchild"])
def test_builtin_namespace_getter_admission_is_not_hidden_by_consumer_identity(
    source: str, unsafe: bool, nested: bool,
) -> None:
    if not unsafe:
        _assert_harmless_runtime_subject_admitted(source, nested)
        return
    base = {"ultimate_ai_agent.subject": "def runtime_value(case): return 1\n"}
    current = {
        "ultimate_ai_agent.subject": "from ultimate_ai_agent.new_child import runtime_value\n",
        "ultimate_ai_agent.new_child": source,
    }
    if nested:
        current["ultimate_ai_agent.new_grandchild"] = source
        current["ultimate_ai_agent.new_child"] = (
            "from ultimate_ai_agent.new_grandchild import runtime_value\n"
        )
    assert _admit_source_graph(base, current, ("ultimate_ai_agent.subject",)) == {}


@pytest.mark.parametrize("alias_scope", ["module", "local"])
@pytest.mark.parametrize("topology", ["existing-app", "child", "unchanged"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_pytest_namespace_alias_consumer_retains_application_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    alias_scope: str, topology: str, snapshot: bool,
) -> None:
    test_source = "import pytest\nfrom ultimate_ai_agent.subject import runtime_value\n"
    if alias_scope == "module":
        test_source += "checks = pytest\n"
    test_source += "def test_case():\n"
    if alias_scope == "local":
        test_source += "    checks = pytest\n"
    test_source += (
        "    value = runtime_value()\n"
        "    if value is None: checks.skip('unavailable')\n    assert value == 1\n"
    )
    changed = "def runtime_value(): return None\n"
    options = (
        {"current_subject": changed, "additions": {}}
        if topology == "existing-app" else
        {"current_subject": "def runtime_value(): return 1\n", "additions": {}}
        if topology == "unchanged" else {"additions": {CHILD_PATH: changed}}
    )
    _install_subject(tmp_path, monkeypatch, test_source, **options)
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    if topology == "unchanged":
        assert removed == ()
    else:
        assert len(removed) == 1
        assert removed[0].startswith(f"{TEST_PATH}::test_case")


@pytest.mark.parametrize("form", ["escaped-getter", "produced-selector"])
@pytest.mark.parametrize("topology", ["existing-app", "child", "unchanged"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_consumer_getter_capability_keeps_application_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    form: str, topology: str, snapshot: bool,
) -> None:
    test_source = (
        "import unittest\nfrom ultimate_ai_agent.subject import runtime_value\n"
        "class TestCase(unittest.TestCase):\n"
        "    def harmless_method(self, reason): return 1\n"
    )
    if form == "escaped-getter":
        test_source += (
            "    def test_case(self): assert runtime_value(getattr, self) == 1\n"
        )
        base_subject = "def runtime_value(lookup, case): return 1\n"
        changed = (
            "def runtime_value(lookup, case): lookup(case, 'skipTest')('unavailable')\n"
        )
    else:
        test_source += (
            "    def test_case(self): assert getattr(self, runtime_value())('unavailable') == 1\n"
        )
        base_subject = "def runtime_value(): return 'harmless_method'\n"
        changed = "def runtime_value(): return 'skipTest'\n"
    current_subject = (
        "from ultimate_ai_agent.new_child import runtime_value\n"
        if topology == "child" else
        base_subject if topology == "unchanged" else changed
    )
    _install_subject(
        tmp_path, monkeypatch, test_source, base_subject=base_subject,
        current_subject=current_subject,
        additions={CHILD_PATH: changed} if topology == "child" else {},
    )
    if topology == "child":
        # The application has no independently recognized getter capability.
        # Its admission must not erase the consumer's strict source identity.
        _assert_harmless_runtime_subject_admitted(changed, False)
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    if topology == "unchanged":
        assert removed == ()
    else:
        assert len(removed) == 1
        assert removed[0].startswith(f"{TEST_PATH}::TestCase::test_case")


@pytest.mark.parametrize("autouse", [False, True], ids=["requested", "autouse"])
@pytest.mark.parametrize("changed", [False, True], ids=["unchanged", "changed"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_imported_fixture_export_name_keeps_injected_abort_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    autouse: bool, changed: bool, snapshot: bool,
) -> None:
    support = {
        "tests/__init__.py": "",
        "tests/helpers.py": (
            "import pytest\nfrom ultimate_ai_agent.subject import runtime_value\n"
            "@pytest.fixture(name='value')\n"
            "def internal_value():\n    value = runtime_value()\n"
            "    if value is None: pytest.skip('unavailable')\n    return value\n"
        ),
    }
    test_source = (
        "import pytest\nfrom tests.helpers import internal_value\n"
        + ("@pytest.fixture(autouse=True)\n" if autouse else "@pytest.fixture\n")
        + "def outer(value): return 1\n"
        + ("def test_case(): assert True\n" if autouse else
           "def test_case(outer): assert outer == 1\n")
    )
    _install_subject(
        tmp_path, monkeypatch, test_source, base_additions=support,
        current_subject=(
            "def runtime_value(): return None\n" if changed else
            "def runtime_value(): return 1\n"
        ), additions={},
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    if changed:
        assert len(removed) == 1
        assert removed[0].startswith(f"{TEST_PATH}::test_case")
    else:
        assert removed == ()


@pytest.mark.parametrize("argument", ["callback", "callback=callback"], ids=["positional", "keyword"])
@pytest.mark.parametrize("scope", ["nested", "module"])
@pytest.mark.parametrize("changed", [False, True], ids=["unchanged", "changed"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_passed_callback_body_preserves_abort_sensitive_producer_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    argument: str, scope: str, changed: bool, snapshot: bool,
) -> None:
    test_source = (
        "import pytest\nfrom ultimate_ai_agent.subject import runtime_value\n"
        "def runner(callback): return callback()\n"
    )
    callback = (
        "def callback():\n    value = runtime_value()\n"
        "    if value is None: pytest.skip('unavailable')\n    return value\n"
    )
    if scope == "nested":
        test_source += "def test_case():\n"
        test_source += "".join("    " + line + "\n" for line in callback.splitlines())
    else:
        test_source += callback + "def test_case():\n"
    test_source += f"    assert runner({argument}) == 1\n"
    _install_subject(
        tmp_path, monkeypatch, test_source,
        current_subject=(
            "def runtime_value(): return None\n" if changed else
            "def runtime_value(): return 1\n"
        ), additions={},
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    if changed:
        assert len(removed) == 1
        assert removed[0].startswith(f"{TEST_PATH}::test_case")
    else:
        assert removed == ()


@pytest.mark.parametrize(
    "form", ["from-package", "direct-module", "mixed-module", "namespace-member", "symbol-alias"]
)
@pytest.mark.parametrize("changed", [False, True], ids=["unchanged", "changed"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_module_value_alias_preserves_exact_consumer_dependency_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    form: str, changed: bool, snapshot: bool,
) -> None:
    test_source = "import pytest\n"
    if form == "symbol-alias":
        test_source += "from ultimate_ai_agent.subject import runtime_value as read_value\n"
    elif form in {"from-package", "mixed-module"}:
        test_source += "from ultimate_ai_agent import subject as subject_module\n"
    else:
        test_source += "import ultimate_ai_agent.subject as subject_module\n"
    module_argument = form in {"from-package", "direct-module", "mixed-module"}
    test_source += (
        "def require_value(module):\n    value = module.runtime_value()\n"
        if module_argument else "def require_value(value):\n"
    )
    test_source += (
        "    if value is None: pytest.skip('unavailable')\n    return value\n"
        "def test_case():\n"
    )
    if form == "mixed-module":
        test_source += "    assert callable(subject_module.runtime_value)\n"
    argument = (
        "subject_module" if module_argument else
        "read_value()" if form == "symbol-alias" else "subject_module.runtime_value()"
    )
    test_source += f"    assert require_value({argument}) == 1\n"
    _install_subject(
        tmp_path, monkeypatch, test_source,
        current_subject=(
            "def runtime_value(): return None\n" if changed else
            "def runtime_value(): return 1\n"
        ), additions={},
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    if changed:
        assert len(removed) == 1
        assert removed[0].startswith(f"{TEST_PATH}::test_case")
    else:
        assert removed == ()


@pytest.mark.parametrize("from_package", [False, True], ids=["direct-module", "from-package"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_module_alias_does_not_resolve_an_absent_static_member(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    from_package: bool, snapshot: bool,
) -> None:
    imported = (
        "from ultimate_ai_agent import subject as subject_module\n" if from_package else
        "import ultimate_ai_agent.subject as subject_module\n"
    )
    test_source = "import pytest\n" + imported + (
        "def test_case():\n    value = subject_module.absent_value()\n"
        "    if value is None: pytest.skip('unavailable')\n    assert value == 1\n"
    )
    _install_subject(
        tmp_path, monkeypatch, test_source,
        current_subject="def runtime_value(): return 1\n", additions={},
    )
    # No source substitution or helper collapse claims to resolve this member.
    # The changed-source counterpart still requires an exact proof refusal.
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    assert guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    ) == ()


@pytest.mark.parametrize("explicit_child", [False, True], ids=["package", "explicit-child"])
@pytest.mark.parametrize("as_value", [False, True], ids=["member-call", "module-value"])
@pytest.mark.parametrize("changed", [False, True], ids=["unchanged", "changed"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_package_namespace_child_retains_runtime_producer_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    explicit_child: bool, as_value: bool, changed: bool, snapshot: bool,
) -> None:
    test_source = "import pytest\n" + (
        "import ultimate_ai_agent.subject\n" if explicit_child else
        "import ultimate_ai_agent\n"
    )
    test_source += (
        "def require_value(owner):\n    value = owner.runtime_value()\n"
        if as_value else "def require_value(value):\n"
    )
    test_source += (
        "    if value is None: pytest.skip('unavailable')\n    return value\n"
        "def test_case():\n"
    )
    argument = (
        "ultimate_ai_agent.subject" if as_value else
        "ultimate_ai_agent.subject.runtime_value()"
    )
    test_source += f"    assert require_value({argument}) == 1\n"
    _install_subject(
        tmp_path, monkeypatch, test_source,
        base_additions={PACKAGE_PATH: "from . import subject\n"},
        current_subject=(
            "def runtime_value(): return None\n" if changed else
            "def runtime_value(): return 1\n"
        ), additions={},
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    if changed:
        assert len(removed) == 1
        assert removed[0].startswith(f"{TEST_PATH}::test_case")
    else:
        assert removed == ()


@pytest.mark.parametrize("member", ["unchanged", "changed", "absent"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_aliased_module_leaf_named_member_is_not_a_namespace_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    member: str, snapshot: bool,
) -> None:
    test_source = (
        "import pytest\nimport ultimate_ai_agent.subject as ultimate_ai_agent\n"
        "def test_case():\n    value = ultimate_ai_agent.subject()\n"
        "    if value is None: pytest.skip('unavailable')\n    assert value == 1\n"
    )
    base_subject = (
        "def unrelated(): return 1\n" if member == "absent" else
        "def subject(): return 1\n"
    )
    _install_subject(
        tmp_path, monkeypatch, test_source, base_subject=base_subject,
        current_subject=(
            "def subject(): return None\n" if member == "changed" else base_subject
        ), additions={},
    )
    # An unchanged absent member is not resolved by ordinary inventory;
    # only a potentially affected consumer needs strict binding proof.
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    if member == "changed":
        assert len(removed) == 1
        assert removed[0].startswith(f"{TEST_PATH}::test_case")
    else:
        assert removed == ()


@pytest.mark.parametrize("direct_module", [False, True], ids=["static-package", "direct-module"])
@pytest.mark.parametrize("changed_source", ["package-member", "child-module"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_package_value_precedence_is_distinct_from_direct_module_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    direct_module: bool, changed_source: str, snapshot: bool,
) -> None:
    test_source = "import pytest\n" + (
        "import ultimate_ai_agent.subject as chosen\n" if direct_module else
        "from ultimate_ai_agent import subject as chosen\n"
    )
    test_source += (
        "def require_value(owner):\n    value = owner.runtime_value()\n"
        "    if value is None: pytest.skip('unavailable')\n    return value\n"
        "def test_case(): assert require_value(chosen) == 1\n"
    )
    package_source = (
        "class Value:\n    def runtime_value(self): return 1\nsubject = Value()\n"
    )
    _install_subject(
        tmp_path, monkeypatch, test_source,
        base_additions={PACKAGE_PATH: package_source},
        current_subject=(
            "def runtime_value(): return None\n" if changed_source == "child-module" else
            "def runtime_value(): return 1\n"
        ), additions={},
    )
    if changed_source == "package-member":
        (tmp_path / PACKAGE_PATH).write_text(
            package_source.replace("return 1", "return None"), encoding="utf-8"
        )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    # A direct module value retains its executed package initializer as part
    # of its conservative source closure, even when that initializer's member
    # is not the selected value. A static package value excludes the dormant child.
    closure_changed = direct_module or changed_source == "package-member"
    if closure_changed:
        assert len(removed) == 1
        assert removed[0].startswith(f"{TEST_PATH}::test_case")
    else:
        assert removed == ()


@pytest.mark.parametrize(
    "imports,expression",
    [
        (
            "import ultimate_ai_agent.decoy\nimport ultimate_ai_agent.subject\n",
            "ultimate_ai_agent.subject.runtime_value()",
        ),
        (
            "import ultimate_ai_agent.decoy\nimport ultimate_ai_agent.subject as ultimate_ai_agent\n",
            "ultimate_ai_agent.runtime_value()",
        ),
        (
            "import ultimate_ai_agent.subject\nimport ultimate_ai_agent.subject as ultimate_ai_agent\n",
            "ultimate_ai_agent.runtime_value()",
        ),
        (
            "import ultimate_ai_agent.decoy as ultimate_ai_agent\nimport ultimate_ai_agent.subject\n",
            "ultimate_ai_agent.subject.runtime_value()",
        ),
    ],
    ids=["same-root-namespaces", "namespace-to-other-alias", "namespace-to-same-alias", "alias-to-namespace"],
)
@pytest.mark.parametrize("changed", [False, True], ids=["unchanged", "changed"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_multiple_import_binding_epochs_retain_active_runtime_subject(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    imports: str, expression: str, changed: bool, snapshot: bool,
) -> None:
    test_source = "import pytest\n" + imports + (
        f"def test_case():\n    value = {expression}\n"
        "    if value is None: pytest.skip('unavailable')\n    assert value == 1\n"
    )
    _install_subject(
        tmp_path, monkeypatch, test_source,
        base_additions={
            "src/ultimate_ai_agent/decoy.py": (
                "def runtime_value(): return 1\n"
                "class Value:\n    def runtime_value(self): return 1\n"
                "subject = Value()\n"
            ),
        },
        current_subject=(
            "def runtime_value(): return None\n" if changed else
            "def runtime_value(): return 1\n"
        ), additions={},
    )
    # An unchanged represented owner needs no runtime equivalence proof.
    if ".decoy" in imports and changed:
        with pytest.raises(
            guard.TestCorpusGuardError,
            match="^ambiguous strict runtime import binding cannot be inventoried safely$",
        ):
            inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
            guard.removed_declarations(tmp_path, BASE_SHA, worktree_snapshot=inventory)
        return
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    if changed:
        assert len(removed) == 1
        assert removed[0].startswith(f"{TEST_PATH}::test_case")
    else:
        assert removed == ()


@pytest.mark.parametrize("changed", [False, True], ids=["unchanged", "changed"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_unused_competing_imports_preserve_independent_consumer_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    changed: bool, snapshot: bool,
) -> None:
    test_source = (
        "import pytest\n"
        "import ultimate_ai_agent.decoy as unused\n"
        "import ultimate_ai_agent.subject as unused\n"
        "from ultimate_ai_agent.subject import runtime_value\n"
        "def test_case():\n    value = runtime_value()\n"
        "    if value is None: pytest.skip('unavailable')\n    assert value == 1\n"
    )
    _install_subject(
        tmp_path, monkeypatch, test_source,
        base_additions={
            "src/ultimate_ai_agent/decoy.py": "def runtime_value(): return 1\n",
        },
        current_subject=(
            "def runtime_value(): return None\n" if changed else
            "def runtime_value(): return 1\n"
        ), additions={},
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    if changed:
        assert len(removed) == 1
        assert removed[0].startswith(f"{TEST_PATH}::test_case")
    else:
        assert removed == ()


@pytest.mark.parametrize("ambiguous", [False, True], ids=["dormant-scope", "referenced-owner"])
@pytest.mark.parametrize("changed", [False, True], ids=["unchanged", "changed"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_transitive_import_owner_keeps_ambiguity_within_referenced_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ambiguous: bool, changed: bool, snapshot: bool,
) -> None:
    helper_source = "import pytest\n"
    if ambiguous:
        helper_source += (
            "import ultimate_ai_agent.decoy as producer\n"
            "import ultimate_ai_agent.subject as producer\n"
        )
    else:
        helper_source += (
            "import ultimate_ai_agent.subject as producer\n"
            "def dormant():\n    import ultimate_ai_agent.decoy as producer\n"
            "    return producer.runtime_value()\n"
        )
    helper_source += (
        "def require_value():\n    value = producer.runtime_value()\n"
        "    if value is None: pytest.skip('unavailable')\n    return value\n"
    )
    _install_subject(
        tmp_path, monkeypatch,
        "from tests.helpers import require_value\n"
        "def test_case(): assert require_value() == 1\n",
        base_additions={
            "tests/__init__.py": "",
            "tests/helpers.py": helper_source,
            "src/ultimate_ai_agent/decoy.py": "def runtime_value(): return 1\n",
        },
        current_subject=(
            "def runtime_value(): return None\n" if changed else
            "def runtime_value(): return 1\n"
        ), additions={},
    )
    if ambiguous and changed:
        with pytest.raises(
            guard.TestCorpusGuardError,
            match="^ambiguous strict runtime import binding cannot be inventoried safely$",
        ):
            inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
            guard.removed_declarations(tmp_path, BASE_SHA, worktree_snapshot=inventory)
        return
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    if changed:
        assert len(removed) == 1
        assert removed[0].startswith(f"{TEST_PATH}::test_case")
    else:
        assert removed == ()


@pytest.mark.parametrize("read_after", [False, True], ids=["read-before", "read-after"])
@pytest.mark.parametrize("changed", [False, True], ids=["unchanged", "changed"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_local_mixed_namespace_alias_binding_is_explicitly_unsupported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    read_after: bool, changed: bool, snapshot: bool,
) -> None:
    test_source = (
        "import pytest\ndef test_case():\n    import ultimate_ai_agent.subject\n"
    )
    if not read_after:
        test_source += "    value = ultimate_ai_agent.subject.runtime_value()\n"
    test_source += "    import ultimate_ai_agent.subject as ultimate_ai_agent\n"
    if read_after:
        test_source += "    value = ultimate_ai_agent.runtime_value()\n"
    test_source += (
        "    if value is None: pytest.skip('unavailable')\n    assert value == 1\n"
    )
    subject = (
        "def runtime_value(): return 1\n"
        "class Value:\n    def runtime_value(self): return 1\nsubject = Value()\n"
    )
    _install_subject(
        tmp_path, monkeypatch, test_source, base_subject=subject,
        current_subject=subject.replace("return 1", "return None", 1) if changed else subject,
        additions={},
    )
    if changed:
        with pytest.raises(
            guard.TestCorpusGuardError,
            match="^ambiguous strict runtime import binding cannot be inventoried safely$",
        ):
            inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
            guard.removed_declarations(tmp_path, BASE_SHA, worktree_snapshot=inventory)
    else:
        inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
        assert guard.removed_declarations(
            tmp_path, BASE_SHA, worktree_snapshot=inventory
        ) == ()


@pytest.mark.parametrize("nested_class", [False, True], ids=["nested-function", "nested-class"])
@pytest.mark.parametrize("changed", [False, True], ids=["unchanged", "changed"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_reachable_nested_callable_retains_its_own_import_dependencies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    nested_class: bool, changed: bool, snapshot: bool,
) -> None:
    helper_source = "def require_value():\n"
    if nested_class:
        helper_source += "    class Callback:\n        def run(self):\n"
        indent = "            "
    else:
        helper_source += "    def callback():\n"
        indent = "        "
    body = (
        "import pytest\nfrom ultimate_ai_agent.subject import runtime_value\n"
        "value = runtime_value()\nif value is None: pytest.skip('unavailable')\n"
        "return value\n"
    )
    helper_source += "".join(indent + line + "\n" for line in body.splitlines())
    helper_source += (
        "    return Callback().run()\n" if nested_class else "    return callback()\n"
    )
    _install_subject(
        tmp_path, monkeypatch,
        "from tests.helpers import require_value\n"
        "def test_case(): assert require_value() == 1\n",
        base_additions={"tests/__init__.py": "", "tests/helpers.py": helper_source},
        current_subject=(
            "def runtime_value(): return None\n" if changed else
            "def runtime_value(): return 1\n"
        ), additions={},
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    if changed:
        assert len(removed) == 1
        assert removed[0].startswith(f"{TEST_PATH}::test_case")
    else:
        assert removed == ()


@pytest.mark.parametrize("changed", [False, True], ids=["unchanged", "changed"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_default_named_imported_fixture_retains_injected_producer_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    changed: bool, snapshot: bool,
) -> None:
    _install_subject(
        tmp_path, monkeypatch,
        "import pytest\nfrom tests.helpers import value\n"
        "@pytest.fixture\ndef outer(value): return value\n"
        "def test_case(outer): assert outer == 1\n",
        base_additions={
            "tests/__init__.py": "",
            "tests/helpers.py": (
                "import pytest\nfrom ultimate_ai_agent.subject import runtime_value\n"
                "@pytest.fixture\ndef value():\n    result = runtime_value()\n"
                "    if result is None: pytest.skip('unavailable')\n    return result\n"
            ),
        },
        current_subject=(
            "def runtime_value(): return None\n" if changed else
            "def runtime_value(): return 1\n"
        ), additions={},
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    if changed:
        assert len(removed) == 1
        assert removed[0].startswith(f"{TEST_PATH}::test_case")
    else:
        assert removed == ()


@pytest.mark.parametrize("scope", ["global", "nonlocal"])
@pytest.mark.parametrize("reached", [False, True], ids=["uncalled", "reached"])
@pytest.mark.parametrize("changed", [False, True], ids=["unchanged", "changed"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_reached_import_installer_write_retains_selected_producer_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    scope: str, reached: bool, changed: bool, snapshot: bool,
) -> None:
    helper_source = "import pytest\n"
    if scope == "global":
        helper_source += (
            "import ultimate_ai_agent.decoy as producer\n"
            "def install():\n    global producer\n"
            "    import ultimate_ai_agent.subject as producer\n"
            "def require_value():\n"
        )
    else:
        helper_source += (
            "def require_value():\n    import ultimate_ai_agent.decoy as producer\n"
            "    def install():\n        nonlocal producer\n"
            "        import ultimate_ai_agent.subject as producer\n"
        )
    if reached:
        helper_source += "    install()\n"
    helper_source += (
        "    value = producer.runtime_value()\n"
        "    if value is None: pytest.skip('unavailable')\n    return value\n"
    )
    _install_subject(
        tmp_path, monkeypatch,
        "from tests.helpers import require_value\n"
        "def test_case(): assert require_value() == 1\n",
        base_additions={
            "tests/__init__.py": "",
            "tests/helpers.py": helper_source,
            "src/ultimate_ai_agent/decoy.py": "def runtime_value(): return 1\n",
        },
        current_subject=(
            "def runtime_value(): return None\n" if changed else
            "def runtime_value(): return 1\n"
        ), additions={},
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    if reached and changed:
        assert len(removed) == 1
        assert removed[0].startswith(f"{TEST_PATH}::test_case")
    else:
        assert removed == ()


@pytest.mark.parametrize("owner", ["test-local", "imported-module"])
@pytest.mark.parametrize("different_source", [False, True], ids=["equivalent", "different-source"])
@pytest.mark.parametrize("changed", [False, True], ids=["unchanged", "changed"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_relative_absolute_imports_use_the_resolved_owner_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    owner: str, different_source: bool, changed: bool, snapshot: bool,
) -> None:
    absolute_source = "tests.decoy" if different_source else "tests.producer"
    imports = (
        "if __package__ in {None, ''}:\n"
        f"    from {absolute_source} import runtime_value\n"
        "else:\n    from .producer import runtime_value\n"
    )
    check = (
        "    value = runtime_value()\n"
        "    if value is None: pytest.skip('unavailable')\n"
    )
    support = {
        "tests/__init__.py": "",
        "tests/producer.py": "from ultimate_ai_agent.subject import runtime_value\n",
        "tests/decoy.py": "def runtime_value(): return 1\n",
    }
    if owner == "test-local":
        test_source = "import pytest\ndef test_case():\n"
        test_source += "".join("    " + line + "\n" for line in imports.splitlines())
        test_source += check + "    assert value == 1\n"
    else:
        support["tests/helpers.py"] = (
            "import pytest\n" + imports + "def require_value():\n"
            + check + "    return value\n"
        )
        test_source = (
            "from tests.helpers import require_value\n"
            "def test_case(): assert require_value() == 1\n"
        )
    _install_subject(
        tmp_path, monkeypatch, test_source, base_additions=support,
        current_subject=(
            "def runtime_value(): return None\n" if changed else
            "def runtime_value(): return 1\n"
        ), additions={},
    )
    # Preserve the earlier ordinary lexical refusal for the local conditional.
    if different_source and (changed or owner == "test-local"):
        reason = (
            "imported runtime helper dependency is ambiguous"
            if owner == "test-local" else
            "ambiguous strict runtime import binding cannot be inventoried safely"
        )
        with pytest.raises(guard.TestCorpusGuardError, match=f"^{reason}$"):
            inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
            guard.removed_declarations(tmp_path, BASE_SHA, worktree_snapshot=inventory)
        return
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    if changed:
        assert len(removed) == 1
        assert removed[0].startswith(f"{TEST_PATH}::test_case")
    else:
        assert removed == ()


@pytest.mark.parametrize("attribute", ["__file__", "__name__"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_ordinary_inventory_does_not_require_unrelated_script_member_proof(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    attribute: str, snapshot: bool,
) -> None:
    _install_subject(
        tmp_path, monkeypatch,
        "import scripts.tool as tool\n"
        f"def test_metadata(): assert tool.{attribute}\n",
        base_additions={
            "scripts/__init__.py": "",
            "scripts/tool.py": "def entry(): return 1\n",
        },
        current_subject="def runtime_value(): return None\n", additions={},
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path)
    assert len(inventory.declarations) == 1
    assert inventory.declarations[0].ref.startswith(f"{TEST_PATH}::test_metadata")
    assert guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory if snapshot else None
    ) == ()


@pytest.mark.parametrize("form", ["helper", "requested-fixture", "callback", "secondary-candidate"])
@pytest.mark.parametrize("changed", [False, True], ids=["unchanged", "changed"])
@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_comparison_proof_tracks_each_cached_consumer_without_unrelated_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    form: str, changed: bool, snapshot: bool,
) -> None:
    support = {
        "tests/__init__.py": "",
        "scripts/__init__.py": "",
        "scripts/tool.py": "def entry(): return 1\n",
    }
    producer_import = "from ultimate_ai_agent.subject import runtime_value\n"
    prefix = "import scripts.tool as tool\n"
    if form == "secondary-candidate":
        support["src/ultimate_ai_agent/package/__init__.py"] = (
            "from ultimate_ai_agent.subject import runtime_value as selected\n"
            "def runtime_value(): return selected()\n"
        )
        support["src/ultimate_ai_agent/package/runtime_value.py"] = (
            "def decoy(): return 9\n"
        )
        producer_import = "from ultimate_ai_agent.package import runtime_value\n"
        prefix += (
            "import ultimate_ai_agent.package.runtime_value as decoy_module\n"
            "def test_decoy(): assert decoy_module.decoy() == 9\n"
        )
    body = (
        "    value = runtime_value()\n"
        "    if value is None: pytest.skip('unavailable')\n"
        "    return value\n"
    )
    if form == "requested-fixture":
        support["tests/helpers.py"] = (
            "import pytest\n" + producer_import
            + "@pytest.fixture\ndef checked_value():\n" + body
        )
        prefix += "from tests.helpers import checked_value\n"
        consumers = (
            "def test_first(checked_value): assert checked_value == 1\n"
            "def test_second(checked_value): assert checked_value == 1\n"
        )
    elif form == "callback":
        prefix += (
            "import pytest\n" + producer_import
            + "def invoke(callback): return callback()\n"
        )
        consumers = ""
        for name in ("first", "second"):
            consumers += f"def test_{name}():\n    def callback():\n"
            consumers += "".join("    " + line + "\n" for line in body.splitlines())
            consumers += "    assert invoke(callback) == 1\n"
    else:
        support["tests/helpers.py"] = (
            "import pytest\n" + producer_import
            + "def require_value():\n" + body
        )
        prefix += "from tests.helpers import require_value\n"
        consumers = (
            "def test_first(): assert require_value() == 1\n"
            "def test_second(): assert require_value() == 1\n"
        )
    _install_subject(
        tmp_path, monkeypatch,
        prefix + consumers + "def test_metadata(): assert tool.__file__\n",
        base_additions=support,
        current_subject=(
            "def runtime_value(): return None\n" if changed else
            "def runtime_value(): return 1\n"
        ), additions={},
    )
    prior_refs: set[str] = set()
    parse_prior = guard._parse_base_test_declarations

    def capture_original_refs(*args, **kwargs):
        declarations = parse_prior(*args, **kwargs)
        prior_refs.update(item.ref for item in declarations)
        return declarations

    monkeypatch.setattr(guard, "_parse_base_test_declarations", capture_original_refs)
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    assert set(removed) <= prior_refs
    if changed:
        assert len(removed) == 2
        assert sum(ref.startswith(f"{TEST_PATH}::test_first") for ref in removed) == 1
        assert sum(ref.startswith(f"{TEST_PATH}::test_second") for ref in removed) == 1
    else:
        assert removed == ()


@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_changed_consumer_with_unresolved_member_cannot_reuse_equal_unknown_proof(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, snapshot: bool,
) -> None:
    _install_subject(
        tmp_path, monkeypatch,
        "import pytest\nimport ultimate_ai_agent.subject as subject\n"
        "def test_case():\n    value = subject.absent_value()\n"
        "    if value is None: pytest.skip('unavailable')\n    assert value == 1\n",
        current_subject="def runtime_value(): return None\n", additions={},
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path)
    assert len(inventory.declarations) == 1
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="^imported Python parameter binding cannot be resolved safely$",
    ):
        guard.removed_declarations(
            tmp_path, BASE_SHA, worktree_snapshot=inventory if snapshot else None
        )


@pytest.mark.parametrize("snapshot", [False, True], ids=["scoped", "snapshot"])
def test_module_object_proof_retains_stable_alternative_wrapper_dependencies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, snapshot: bool,
) -> None:
    _install_subject(
        tmp_path, monkeypatch,
        "import pytest\nimport tests.helpers as owner\n"
        "def consume(module):\n    value = module.require_value()\n"
        "    if value is None: pytest.skip('unavailable')\n    return value\n"
        "def test_case(): assert consume(owner) == 1\n",
        base_additions={
            "tests/__init__.py": "",
            "tests/helpers.py": (
                "import ultimate_ai_agent.decoy as producer\n"
                "import ultimate_ai_agent.active as producer\n"
                "def require_value(): return producer.runtime_value()\n"
            ),
            "src/ultimate_ai_agent/decoy.py": "def runtime_value(): return 1\n",
            "src/ultimate_ai_agent/active.py": (
                "from ultimate_ai_agent.subject import runtime_value\n"
            ),
        },
        current_subject="def runtime_value(): return None\n", additions={},
    )
    inventory = guard._inventory_worktree_snapshot(tmp_path) if snapshot else None
    removed = guard.removed_declarations(
        tmp_path, BASE_SHA, worktree_snapshot=inventory
    )
    assert len(removed) == 1
    assert removed[0].startswith(f"{TEST_PATH}::test_case")


@pytest.mark.parametrize("over_budget", [False, True], ids=["within-budget", "over-budget"])
def test_opaque_consumer_capture_enforces_existing_module_budget(
    monkeypatch: pytest.MonkeyPatch, over_budget: bool,
) -> None:
    source = "import scripts.tool as tool\ndef test_metadata(): assert tool.__file__\n"
    sources = {
        TEST_PATH: source,
        "tests/__init__.py": "",
        "scripts/__init__.py": "",
        "scripts/tool.py": "import scripts.chain0\n",
    }
    size = 12 if over_budget else 1
    sources.update({
        f"scripts/chain{index}.py": (
            f"import scripts.chain{index + 1}\n" if index + 1 < size else "VALUE = 1\n"
        )
        for index in range(size)
    })
    resolver = guard._python_import_resolver(sources.get)
    monkeypatch.setattr(guard, "MAX_PYTHON_DEPENDENCY_MODULES", 8)
    ordinary = tuple(guard._python_inventory_entries(TEST_PATH, source, resolver))
    assert len(ordinary) == 1
    # This focused metadata entry point excludes the whole-repository census;
    # its refusal must come from the opaque certificate's actual source walk.
    certificate = guard._PythonConsumerCertificate(resolver, resolver, resolver)
    proofs: dict[str, str] = {}
    if over_budget:
        with pytest.raises(
            guard.TestCorpusGuardError,
            match="^runtime consumer certificate exceeds module budget$",
        ):
            tuple(guard._python_inventory_entries(
                TEST_PATH, source, resolver, runtime_consumer_proofs=proofs,
                runtime_consumer_certificate=certificate,
            ))
    else:
        represented = tuple(guard._python_inventory_entries(
            TEST_PATH, source, resolver, runtime_consumer_proofs=proofs,
            runtime_consumer_certificate=certificate,
        ))
        assert len(represented) == len(ordinary)
        assert not certificate.requires_proof(f"{TEST_PATH}::test_metadata")


def test_certificate_module_roots_share_source_and_import_edge_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work_by_size: dict[int, int] = {}
    import_modules = guard._python_import_modules
    for size in (8, 16, 32):
        modules = tuple(f"module_{index}" for index in range(size))
        sources = {
            f"{module}.py": (
                f"import {modules[index + 1]}\nVALUE = 1\n"
                if index + 1 < size else "VALUE = 1\n"
            )
            for index, module in enumerate(modules)
        }
        resolver = guard._python_import_resolver(sources.get)
        certificate = guard._PythonConsumerCertificate(resolver, resolver, resolver)
        source_visits = 0
        edge_visits = 0
        expanded_modules: set[str] = set()

        def count_import_construction(tree, *, relative_package):
            nonlocal source_visits, edge_visits
            imports = import_modules(tree, relative_package=relative_package)
            source_visits += 1
            edge_visits += sum(len(candidates) for candidates in imports.values())
            expanded_modules.add(relative_package)
            return imports

        with monkeypatch.context() as counted:
            counted.setattr(guard, "_python_import_modules", count_import_construction)
            for module in modules:
                source = resolver(module)
                assert source is not None
                certificate.capture(
                    ("consumer", module),
                    lambda module=module, source=source: guard._python_module_dependency_identity(
                        module, source, certificate.resolver
                    ),
                )
            assert all(not certificate.requires_proof(module) for module in modules)
        assert expanded_modules == set(modules)
        work_by_size[size] = source_visits + edge_visits
    # Count certificate source/edge construction only. Strict identity proofs
    # have separate costs; no wall-clock or universal complexity claim is made.
    assert all(work <= 4 * (size + size - 1) for size, work in work_by_size.items())
    assert work_by_size[16] <= 2 * work_by_size[8] + 8
    assert work_by_size[32] <= 2 * work_by_size[16] + 8
