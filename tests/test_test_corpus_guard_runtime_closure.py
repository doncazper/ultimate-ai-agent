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
