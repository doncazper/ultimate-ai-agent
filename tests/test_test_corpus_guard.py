import hashlib
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from scripts.verification import test_corpus_guard as guard
from scripts.verification import test_corpus_frontend as frontend


VERIFICATION_ENVELOPE = "github-verification-envelope:test-fixture"


def _source_ref(test_ref: str) -> str:
    return guard.build_test_source_ref(test_ref, f"verified-source:{test_ref}")


def _validate_envelope(value: str, _replacement_refs: list[str]) -> None:
    if value != VERIFICATION_ENVELOPE:
        raise ValueError("verification envelope is invalid")


def _validate_retirements(*args: object, **kwargs: object) -> int:
    return guard.validate_retirements(
        *args,
        resolve_assertion_source_ref=_source_ref,
        validate_verification_envelope=_validate_envelope,
        **kwargs,
    )


def _record(
    retired_ref: str,
    replacement_ref: str,
) -> dict[str, object]:
    replacement_refs = [replacement_ref]
    assertion_artifact = {
        "schema_version": guard.ASSERTION_EVIDENCE_SCHEMA,
        "replacement_ref": replacement_ref,
        "source_ref": _source_ref(replacement_ref),
    }
    result_artifact = {
        "schema_version": guard.TEST_RESULT_EVIDENCE_SCHEMA,
        "verified_refs": replacement_refs,
        "verification_envelope": VERIFICATION_ENVELOPE,
    }
    equivalence_artifact = {
        "schema_version": guard.ASSERTION_EQUIVALENCE_SCHEMA,
        "retired_ref": retired_ref,
        "replacement_refs": replacement_refs,
        "preserved_assertion_evidence": [
            {
                "artifact": assertion_artifact,
                "ref": guard.retirement_artifact_ref(
                    "assertion-ref", assertion_artifact
                ),
            }
        ],
    }
    evidence_artifact = {
        "schema_version": guard.RETIREMENT_EVIDENCE_SCHEMA,
        "retired_ref": retired_ref,
        "replacement_refs": replacement_refs,
        "verification_evidence": [
            {
                "artifact": result_artifact,
                "ref": guard.retirement_artifact_ref(
                    "test-result-ref", result_artifact
                ),
            }
        ],
    }
    return {
        "retired_ref": retired_ref,
        "replacement_refs": replacement_refs,
        "reason": "The replacement preserves the same exact defect class.",
        "assertion_equivalence_artifact": equivalence_artifact,
        "assertion_equivalence_ref": guard.retirement_artifact_ref(
            "assertion-equivalence-ref",
            equivalence_artifact,
        ),
        "evidence_artifact": evidence_artifact,
        "evidence_ref": guard.retirement_artifact_ref(
            "test-corpus-evidence-ref",
            evidence_artifact,
        ),
    }


def test_python_inventory_includes_module_async_and_class_tests() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        """
def test_sync():
    assert True

async def test_async():
    assert True

class TestGroup:
    def test_method(self):
        assert True

def helper():
    pass
""",
    )

    assert [item.ref for item in declarations] == [
        "tests/test_sample.py::test_sync",
        "tests/test_sample.py::test_async",
        "tests/test_sample.py::TestGroup::test_method",
    ]


def test_python_inventory_matches_inherited_pytest_class_collection() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        """
class Base:
    def test_inherited(self):
        assert True

class TestChild(Base):
    pass
""",
    )

    assert [item.ref for item in declarations] == [
        "tests/test_sample.py::TestChild::test_inherited",
    ]


def test_python_inventory_binds_parameterized_decorator_changes() -> None:
    path = "tests/test_sample.py"
    before = guard.parse_python_declarations(
        path,
        """
import pytest

@pytest.mark.parametrize("value", ["one", "two"])
def test_case(value):
    assert value
""",
    )
    after = guard.parse_python_declarations(
        path,
        """
import pytest

@pytest.mark.parametrize("value", ["one"])
def test_case(value):
    assert value
""",
    )

    assert len(before) == len(after) == 1
    assert before[0].ref.startswith(f"{path}::test_case::parametrize-sha256:")
    assert after[0].ref.startswith(f"{path}::test_case::parametrize-sha256:")
    assert before[0].ref != after[0].ref


def test_python_inventory_binds_fixture_consumption_changes() -> None:
    path = "tests/test_sample.py"
    fixture_ref = guard.parse_python_declarations(
        path,
        "def test_case(shared_value): pass\n",
    )[0].ref
    plain_ref = guard.parse_python_declarations(
        path,
        "def test_case(): pass\n",
    )[0].ref

    assert fixture_ref != plain_ref


def test_python_inventory_binds_usefixtures_changes() -> None:
    path = "tests/test_sample.py"
    first_ref = guard.parse_python_declarations(
        path,
        'import pytest\n@pytest.mark.usefixtures("first")\ndef test_case(): pass\n',
    )[0].ref
    second_ref = guard.parse_python_declarations(
        path,
        'import pytest\n@pytest.mark.usefixtures("second")\ndef test_case(): pass\n',
    )[0].ref

    assert first_ref != second_ref


def test_python_inventory_binds_module_parameter_data_changes() -> None:
    path = "tests/test_sample.py"
    template = """
import pytest

CASES = {cases}

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value
"""
    before = guard.parse_python_declarations(
        path,
        template.format(cases='["one", "two"]'),
    )
    after = guard.parse_python_declarations(
        path,
        template.format(cases='["one"]'),
    )

    assert before[0].ref != after[0].ref


def test_python_inventory_binds_module_parameter_mutations() -> None:
    path = "tests/test_sample.py"
    before = guard.parse_python_declarations(
        path,
        """
import pytest

CASES = ["one"]
CASES += ["two"]
CASES.append("three")

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value
""",
    )
    after_augassign_removal = guard.parse_python_declarations(
        path,
        """
import pytest

CASES = ["one"]
CASES.append("three")

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value
""",
    )
    after_append_removal = guard.parse_python_declarations(
        path,
        """
import pytest

CASES = ["one"]
CASES += ["two"]

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value
""",
    )
    after_mutation_reorder = guard.parse_python_declarations(
        path,
        """
import pytest

CASES = ["one"]
CASES.append("three")
CASES += ["two"]

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value
""",
    )

    assert before[0].ref != after_augassign_removal[0].ref
    assert before[0].ref != after_append_removal[0].ref
    assert before[0].ref != after_mutation_reorder[0].ref


def test_python_inventory_binds_parameter_mutations_after_declaration() -> None:
    path = "tests/test_sample.py"
    before = guard.parse_python_declarations(
        path,
        """
import pytest

CASES = ["one"]

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value

CASES.append("two")
""",
    )
    after = guard.parse_python_declarations(
        path,
        """
import pytest

CASES = ["one"]

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value

CASES.append("three")
""",
    )

    assert before[0].ref != after[0].ref


def test_python_inventory_ignores_parameter_rebindings_after_declaration() -> None:
    path = "tests/test_sample.py"
    template = """
import pytest

CASES = ["one"]

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value

CASES = {replacement}
CASES.append({appended})
"""
    before = guard.parse_python_declarations(
        path, template.format(replacement='["two"]', appended='"four"')
    )
    after = guard.parse_python_declarations(
        path, template.format(replacement='["three"]', appended='"five"')
    )

    assert before[0].ref == after[0].ref


def test_python_inventory_binds_parameter_data_builder_changes() -> None:
    path = "tests/test_sample.py"
    template = """
import pytest

def build_cases():
    return {cases}

CASES = build_cases()

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value
"""
    before = guard.parse_python_declarations(
        path,
        template.format(cases='["one", "two"]'),
    )
    after = guard.parse_python_declarations(
        path,
        template.format(cases='["one"]'),
    )

    assert before[0].ref != after[0].ref


def test_python_inventory_binds_parametrize_alias_and_class_data() -> None:
    path = "tests/test_sample.py"
    alias_template = """
import pytest

parameterize = pytest.mark.parametrize

@parameterize("value", {cases})
def test_case(value):
    assert value
"""
    before = guard.parse_python_declarations(
        path, alias_template.format(cases='["one", "two"]')
    )
    after = guard.parse_python_declarations(
        path, alias_template.format(cases='["one"]')
    )
    assert before[0].ref != after[0].ref

    imported_before = guard.parse_python_declarations(
        path,
        alias_template.format(cases='["one", "two"]')
        .replace("import pytest", "from pytest.mark import parametrize")
        .replace(
            "parameterize = pytest.mark.parametrize\n\n@parameterize",
            "@parametrize",
        ),
    )
    imported_after = guard.parse_python_declarations(
        path,
        alias_template.format(cases='["one"]')
        .replace("import pytest", "from pytest.mark import parametrize")
        .replace(
            "parameterize = pytest.mark.parametrize\n\n@parameterize",
            "@parametrize",
        ),
    )
    assert imported_before[0].ref != imported_after[0].ref

    class_before = guard.parse_python_declarations(
        path,
        alias_template.format(cases='["one", "two"]')
        .replace(
            "def test_case(value):", "class TestCases:\n    def test_case(self, value):"
        )
        .replace("    assert value", "        assert value"),
    )
    class_after = guard.parse_python_declarations(
        path,
        alias_template.format(cases='["one"]')
        .replace(
            "def test_case(value):", "class TestCases:\n    def test_case(self, value):"
        )
        .replace("    assert value", "        assert value"),
    )
    assert class_before[0].ref != class_after[0].ref


def test_python_inventory_rejects_pytest_generate_tests() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="pytest_generate_tests cannot be inventoried safely",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            """
def pytest_generate_tests(metafunc):
    metafunc.parametrize("value", ["one", "two"])

def test_case(value):
    assert value
""",
        )


def test_python_inventory_rejects_imported_parameter_data() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="imported Python parameter data cannot be inventoried safely",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            """
import pytest
from data import CASES

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value
""",
        )


@pytest.mark.parametrize(
    "source",
    (
        'import importlib\nCASES = importlib.import_module("tests.cases").CASES\n',
        "from importlib import import_module\n"
        'CASES = import_module("tests.cases").CASES\n',
        "import importlib\n"
        "load_cases = importlib.import_module\n"
        "load_cases_alias = load_cases\n"
        'CASES = load_cases_alias("tests.cases").CASES\n',
    ),
)
def test_python_inventory_rejects_dynamic_parameter_imports(source: str) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic Python parameter imports",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            source
            + """
import pytest

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value
""",
        )


def test_python_inventory_rejects_unresolved_collected_class_base() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="test class base cannot be resolved safely",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            """
from helpers import Base

class TestChild(Base):
    pass
""",
        )


def test_python_inventory_rejects_unresolved_ancestor_of_inherited_test() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="test class base cannot be resolved safely",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            """
from helpers import ExternalBase

class Base(ExternalBase):
    def test_inherited(self):
        pass

class TestChild(Base):
    pass
""",
        )


def test_python_inventory_rejects_unresolved_ancestor_before_constructor_skip() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="test class base cannot be resolved safely",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            """
from helpers import ExternalBase

class Base(ExternalBase):
    def __init__(self):
        pass

class TestChild(Base):
    pass
""",
        )


def test_python_inventory_skips_builtin_exception_classes() -> None:
    assert (
        guard.parse_python_declarations(
            "scripts/test_evidence.py",
            """
class TestEvidenceError(RuntimeError):
    pass
""",
        )
        == ()
    )


def test_python_inventory_skips_dataclass_with_generated_constructor() -> None:
    assert (
        guard.parse_python_declarations(
            "scripts/test_contract.py",
            """
from dataclasses import dataclass

@dataclass(frozen=True)
class TestContract:
    value: str
""",
        )
        == ()
    )


def test_python_inventory_rejects_callable_test_name_assignment() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="test-name assignment cannot be inventoried safely",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            """
def check():
    pass

test_case = check
""",
        )


def test_python_inventory_collects_unittest_testcase_regardless_name() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        """
import unittest as unit

class WidgetCases(unit.TestCase):
    def test_widget(self):
        assert True
""",
    )

    assert [item.ref for item in declarations] == [
        "tests/test_sample.py::WidgetCases::test_widget"
    ]


def test_python_inventory_collects_unittest_testcase_through_module_alias() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        "import unittest as u\n"
        "alias = u\n"
        "class WidgetCases(alias.TestCase):\n"
        "    def test_widget(self): pass\n",
    )

    assert [item.ref for item in declarations] == [
        "tests/test_sample.py::WidgetCases::test_widget"
    ]


@pytest.mark.parametrize(
    "alias_assignment",
    (
        "Case = unittest.TestCase",
        "Case = unittest.TestCase\nTransitiveCase = Case",
        "(Case,) = (unittest.TestCase,)",
    ),
)
def test_python_inventory_collects_assigned_unittest_testcase_aliases(
    alias_assignment: str,
) -> None:
    base_name = "TransitiveCase" if "TransitiveCase" in alias_assignment else "Case"
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        "import unittest\n"
        f"{alias_assignment}\n"
        f"class WidgetCases({base_name}):\n"
        "    def test_widget(self): pass\n",
    )

    assert [item.ref for item in declarations] == [
        "tests/test_sample.py::WidgetCases::test_widget"
    ]


@pytest.mark.parametrize(
    ("alias_assignment", "base"),
    (
        ('Case = getattr(unittest, "TestCase")', "Case"),
        (
            'Case = unittest.TestCase\nCase = getattr(unittest, "TestCase")',
            "Case",
        ),
        (
            'RawCase = getattr(unittest, "TestCase")\nCase = RawCase',
            "Case",
        ),
        (
            'Case = RawCase\nRawCase = getattr(unittest, "TestCase")',
            "Case",
        ),
        (
            "Case = unittest.TestCase\n"
            'Case = getattr(unittest, "TestCase")\nAlias = Case',
            "Alias",
        ),
        (
            '(Case, OtherCase) = (getattr(unittest, "TestCase"), unittest.TestCase)',
            "Case",
        ),
        (
            "from unittest import TestCase as BaseCase\nCase = identity(BaseCase)",
            "Case",
        ),
        ("", 'getattr(unittest, "TestCase")'),
    ),
)
def test_python_inventory_rejects_dynamic_unittest_testcase_alias(
    alias_assignment: str,
    base: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic unittest.TestCase alias",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "import unittest\n"
            f"{alias_assignment}\n"
            f"class WidgetCases({base}):\n"
            "    def test_widget(self): pass\n",
        )


def test_python_inventory_rejects_rebound_unittest_testcase_alias() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic unittest.TestCase alias",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "import unittest\n"
            "Case = unittest.TestCase\n"
            "Case = object\n"
            "class WidgetCases(Case):\n"
            "    def test_widget(self): pass\n",
        )


def test_python_inventory_rejects_loop_rebound_unittest_testcase_alias() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match=r"dynamic unittest\.TestCase alias",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "import unittest\n"
            "Case = unittest.TestCase\n"
            "for Case in [object]: pass\n"
            "class WidgetCases(Case):\n"
            "    def test_widget(self): pass\n",
        )


@pytest.mark.parametrize(
    "definition",
    (
        "def helper(value=(Case := object)): pass",
        "@((Case := object))\ndef helper(): pass",
    ),
)
def test_python_inventory_rejects_definition_time_unittest_alias_rebinding(
    definition: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match=r"dynamic unittest\.TestCase alias",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "import unittest\n"
            "Case = unittest.TestCase\n"
            f"{definition}\n"
            "class WidgetCases(Case):\n"
            "    def test_widget(self): pass\n",
        )


def test_python_inventory_binds_global_mutation_helpers_not_read_only_uses() -> None:
    path = "tests/test_sample.py"
    template = """
import pytest

CASES = ["one"]

def add_cases():
    CASES.append({case})

add_cases()
{diagnostic}

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value
"""
    before = guard.parse_python_declarations(
        path, template.format(case='"two"', diagnostic="print(CASES)")
    )
    helper_change = guard.parse_python_declarations(
        path, template.format(case='"three"', diagnostic="print(CASES)")
    )
    read_only_change = guard.parse_python_declarations(
        path, template.format(case='"two"', diagnostic="assert CASES")
    )
    read_only_method_before = guard.parse_python_declarations(
        path, template.format(case='"two"', diagnostic="CASES.copy()")
    )
    read_only_method_after = guard.parse_python_declarations(
        path, template.format(case='"two"', diagnostic='CASES.count("one")')
    )

    assert before[0].ref != helper_change[0].ref
    assert before[0].ref == read_only_change[0].ref
    assert read_only_method_before[0].ref == read_only_method_after[0].ref


def test_python_inventory_matches_test_prefix_and_disabled_declarations() -> None:
    path = "tests/test_sample.py"
    declarations = guard.parse_python_declarations(
        path,
        """
def test():
    pass

def testCamelCase():
    pass

def test_disabled():
    pass

test_disabled.__test__ = False

def test_rebound():
    pass

test_rebound = object()

def test_deleted():
    pass

del test_deleted
""",
    )

    assert [declaration.ref for declaration in declarations] == [
        f"{path}::test",
        f"{path}::testCamelCase",
    ]

    class_declarations = guard.parse_python_declarations(
        path,
        """
class Base:
    def test_inherited(self):
        pass

class TestCases(Base):
    test_inherited = None

    def test_disabled(self):
        pass

    test_disabled.__test__ = False
""",
    )
    assert class_declarations == ()


@pytest.mark.parametrize("disabled_value", ("False", "None", "0", "0.0", "''", "[]"))
def test_python_inventory_treats_static_falsy_test_values_as_disabled(
    disabled_value: str,
) -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        f"def test_disabled(): pass\ntest_disabled.__test__ = {disabled_value}\n",
    )

    assert declarations == ()


def test_python_inventory_tracks_unpacked_and_reenabled_test_values() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        "def test_disabled(): pass\n"
        "(test_disabled.__test__, marker) = (0, object())\n"
        "def test_enabled(): pass\n"
        "test_enabled.__test__ = False\n"
        "test_enabled.__test__ = True\n",
    )

    assert [item.ref for item in declarations] == ["tests/test_sample.py::test_enabled"]


def test_python_inventory_rejects_dynamic_function_test_mutation() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic Python function __test__ mutation",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "def test_case(): pass\ntest_case.__test__ = enabled\n",
        )


@pytest.mark.parametrize(
    "alias_assignment",
    (
        "Alias = test_case",
        "Intermediate = test_case\nAlias = Intermediate",
        "(Alias, marker) = (test_case, object())",
    ),
)
def test_python_inventory_tracks_function_alias_test_mutation(
    alias_assignment: str,
) -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        f"def test_case(): pass\n{alias_assignment}\nAlias.__test__ = False\n",
    )

    assert declarations == ()


def test_python_inventory_tracks_walrus_function_alias_mutation() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        "def test_case(): pass\n(Alias := test_case).__test__ = False\n",
    )

    assert declarations == ()


def test_python_inventory_binds_runtime_pytest_skip_body() -> None:
    path = "tests/test_sample.py"
    active = guard.parse_python_declarations(
        path,
        "def test_case():\n    pass\n",
    )[0].ref
    skipped = guard.parse_python_declarations(
        path,
        "import pytest\ndef test_case():\n    pytest.skip('disabled')\n",
    )[0].ref

    assert active != skipped

    aliased = guard.parse_python_declarations(
        path,
        "import pytest\ndef test_case():\n"
        "    q = pytest\n"
        "    stop = q.skip\n"
        "    stop('disabled')\n",
    )[0].ref
    assert active != aliased

    invoked = guard.parse_python_declarations(
        path,
        "import pytest\ndef test_case():\n"
        "    pytest.skip.__call__('disabled')\n",
    )[0].ref
    assert active != invoked


@pytest.mark.parametrize(
    "runtime_xfail",
    (
        "import pytest\ndef test_case():\n    pytest.xfail('disabled')\n",
        "from pytest import xfail as stop\ndef test_case():\n    stop('disabled')\n",
        "import pytest\ndef test_case():\n"
        "    q = pytest\n    stop = q.xfail\n    stop('disabled')\n",
        "import pytest\ndef test_case():\n"
        "    stop = getattr(pytest, 'xfail')\n    stop('disabled')\n",
    ),
)
def test_python_inventory_binds_runtime_pytest_xfail_body(
    runtime_xfail: str,
) -> None:
    path = "tests/test_sample.py"
    active = guard.parse_python_declarations(
        path,
        "def test_case():\n    pass\n",
    )[0].ref
    xfailed = guard.parse_python_declarations(path, runtime_xfail)[0].ref

    assert active != xfailed


def test_python_inventory_binds_runtime_pytest_xfail_exception() -> None:
    path = "tests/test_sample.py"
    active = guard.parse_python_declarations(path, "def test_case():\n    pass\n")[
        0
    ].ref
    xfailed = guard.parse_python_declarations(
        path,
        "import pytest\ndef test_case():\n"
        "    raise pytest.xfail.Exception('disabled')\n",
    )[0].ref

    assert active != xfailed


@pytest.mark.parametrize(
    "runtime_xfail",
    (
        "import pytest\ndef test_case():\n    raise pytest.xfail.Exception\n",
        "import pytest\ndef test_case():\n"
        "    X = pytest.xfail.Exception\n    raise X\n",
    ),
)
def test_python_inventory_binds_bare_runtime_pytest_xfail_exception(
    runtime_xfail: str,
) -> None:
    path = "tests/test_sample.py"
    active = guard.parse_python_declarations(path, "def test_case():\n    pass\n")[
        0
    ].ref
    xfailed = guard.parse_python_declarations(path, runtime_xfail)[0].ref

    assert active != xfailed


@pytest.mark.parametrize(
    "runtime_xfail",
    (
        "import pytest\ndef test_case():\n"
        "    raise getattr(pytest.xfail, 'Exception')\n",
        "import pytest\ndef test_case():\n"
        "    X = getattr(pytest.xfail, 'Exception')\n    raise X\n",
        "import pytest\nfrom builtins import getattr as lookup\n"
        "def test_case():\n    X = lookup(pytest.xfail, 'Exception')\n    raise X\n",
    ),
)
def test_python_inventory_binds_dynamic_runtime_pytest_xfail_exception(
    runtime_xfail: str,
) -> None:
    path = "tests/test_sample.py"
    active = guard.parse_python_declarations(path, "def test_case():\n    pass\n")[
        0
    ].ref
    xfailed = guard.parse_python_declarations(path, runtime_xfail)[0].ref

    assert active != xfailed


@pytest.mark.parametrize(
    "test_source",
    (
        "def stop():\n    return None\ndef test_case():\n    stop()\n",
        "def test_case():\n    def stop():\n        return None\n    stop()\n",
    ),
)
def test_python_inventory_binds_local_runtime_xfail_helper(
    test_source: str,
) -> None:
    path = "tests/test_sample.py"
    active = guard.parse_python_declarations(path, test_source)[0].ref
    xfailed_source = test_source.replace("return None", "pytest.xfail('disabled')")
    xfailed = guard.parse_python_declarations(
        path,
        "import pytest\n" + xfailed_source,
    )[0].ref

    assert active != xfailed


def test_python_inventory_binds_imported_runtime_xfail_helper() -> None:
    test_source = "from tests.helper import stop\ndef test_case():\n    stop()\n"

    def ref_for(helper_source: str) -> str:
        resolver = guard._python_import_resolver(
            lambda path: helper_source if path == "tests/helper.py" else None
        )
        return guard._python_inventory_entries(
            "tests/test_example.py", test_source, resolver
        )[0][0].ref

    assert ref_for("def stop():\n    return None\n") != ref_for(
        "import pytest\ndef stop():\n    pytest.xfail('disabled')\n"
    )


def test_python_inventory_binds_static_callable_container_targets() -> None:
    path = "tests/test_example.py"
    direct_active = guard.parse_python_declarations(
        path,
        "def test_case():\n    callbacks = (lambda: None,)\n    callbacks[0]()\n",
    )[0].ref
    direct_xfail = guard.parse_python_declarations(
        path,
        "import pytest\ndef test_case():\n    callbacks = (pytest.xfail,)\n"
        "    callbacks[0]('disabled')\n",
    )[0].ref
    local_active = guard.parse_python_declarations(
        path,
        "def stop():\n    return None\ndef test_case():\n"
        "    callbacks = [stop]\n    callbacks[0]()\n",
    )[0].ref
    local_xfail = guard.parse_python_declarations(
        path,
        "import pytest\ndef stop():\n    pytest.xfail('disabled')\n"
        "def test_case():\n    callbacks = [stop]\n    callbacks[0]()\n",
    )[0].ref

    test_source = (
        "from tests.helper import stop\ndef test_case():\n"
        "    callbacks = {'stop': stop}\n    callbacks['stop']()\n"
    )

    def imported_ref(helper_source: str) -> str:
        resolver = guard._python_import_resolver(
            lambda candidate: helper_source if candidate == "tests/helper.py" else None
        )
        return guard._python_inventory_entries(path, test_source, resolver)[0][0].ref

    assert direct_active != direct_xfail
    assert local_active != local_xfail
    assert imported_ref("def stop():\n    return None\n") != imported_ref(
        "import pytest\ndef stop():\n    pytest.xfail('disabled')\n"
    )


@pytest.mark.parametrize(
    ("active_container", "xfail_container", "invocation"),
    (
        (
            "((lambda: None,),)",
            "((pytest.xfail,),)",
            "callbacks[0][0]('disabled')",
        ),
        (
            "{'group': {'stop': lambda: None}}",
            "{'group': {'stop': pytest.xfail}}",
            "callbacks.get('group').get('stop')('disabled')",
        ),
    ),
)
def test_python_inventory_binds_nested_static_callable_container_targets(
    active_container: str,
    xfail_container: str,
    invocation: str,
) -> None:
    path = "tests/test_example.py"
    active = guard.parse_python_declarations(
        path,
        f"def test_case():\n    callbacks = {active_container}\n    {invocation}\n",
    )[0].ref
    xfailed = guard.parse_python_declarations(
        path,
        "import pytest\n"
        f"def test_case():\n    callbacks = {xfail_container}\n    {invocation}\n",
    )[0].ref

    assert active != xfailed


@pytest.mark.parametrize(
    "mutation",
    (
        "callbacks[0] = pytest.xfail",
        "alias = callbacks\n    alias[0] = pytest.xfail",
        "callbacks.append(pytest.xfail)",
        "del callbacks[0]",
    ),
)
def test_python_inventory_rejects_mutated_static_callable_container(
    mutation: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic runtime helper container",
    ):
        guard.parse_python_declarations(
            "tests/test_example.py",
            "import pytest\ndef test_case():\n"
            "    callbacks = [lambda: None]\n"
            f"    {mutation}\n"
            "    callbacks[0]()\n",
        )


def test_python_inventory_allows_ordinary_noncallable_container_mutation() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_example.py",
        "import sys\n"
        "import weakref\n"
        "def test_case(run):\n"
        "    values = [1]\n"
        "    values.append(2)\n"
        "    payload = {'seen': False}\n"
        "    payload.update({'seen': True})\n"
        "    command = [sys.executable, 'script.py']\n"
        "    run(command)\n"
        "    process_lock = object()\n"
        "    assert weakref.ref(process_lock)() is process_lock\n",
    )

    assert len(declarations) == 1


def test_python_inventory_allows_loop_bound_data_in_subscript_assignment() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_example.py",
        "def test_case(request):\n"
        "    cases = [[{'step': 1}], [{'step': 2}]]\n"
        "    for steps in cases:\n"
        "        payload = request.model_dump(mode='python')\n"
        "        payload['steps'] = steps\n"
        "        assert payload['steps'] == steps\n",
    )

    assert len(declarations) == 1


def test_python_inventory_allows_loop_bound_data_appended_to_empty_list() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_example.py",
        "def test_case():\n"
        "    values = []\n"
        "    for value in ('first', 'second'):\n"
        "        values.append(value)\n"
        "    assert values == ['first', 'second']\n",
    )

    assert len(declarations) == 1


def test_python_inventory_allows_annotation_without_assignment_value() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_example.py",
        "def test_case():\n"
        "    values: list[str]\n"
        "    values = ['ready']\n"
        "    assert values\n",
    )

    assert len(declarations) == 1


@pytest.mark.parametrize(
    "source",
    (
        "def test_case():\n"
        "    for callback in (lambda: None,):\n"
        "        callbacks = [callback]\n"
        "        callbacks[0]()\n",
        "def test_case():\n"
        "    callbacks = {}\n"
        "    for callback in (lambda: None,):\n"
        "        callbacks['run'] = callback\n"
        "        callbacks['run']()\n",
        "def test_case():\n"
        "    callbacks = []\n"
        "    for callback in (lambda: None,):\n"
        "        callbacks.append(callback)\n"
        "        callbacks[0]()\n",
    ),
)
def test_python_inventory_rejects_ambiguous_loop_bound_callback_container(
    source: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic runtime helper container",
    ):
        guard.parse_python_declarations("tests/test_example.py", source)


def test_python_inventory_allows_non_aborting_local_callback_registry() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_example.py",
        "_REGISTRY = {}\n"
        "def test_case():\n"
        "    def callback():\n"
        "        return None\n"
        "    _REGISTRY[object()] = ('safe-ref', callback)\n",
    )

    assert len(declarations) == 1


def test_python_inventory_rejects_aborting_local_callback_registry() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic runtime helper container",
    ):
        guard.parse_python_declarations(
            "tests/test_example.py",
            "import pytest\n"
            "_REGISTRY = {}\n"
            "def test_case():\n"
            "    def callback():\n"
            "        pytest.xfail('blocked')\n"
            "    _REGISTRY[object()] = ('safe-ref', callback)\n",
        )


@pytest.mark.parametrize(
    "source",
    (
        "import pytest\ndef test_case():\n"
        "    stop = pytest.xfail\n    callbacks = [stop]\n"
        "    callbacks[0]('blocked')\n",
        "import pytest\ndef test_case():\n"
        "    callbacks = [pytest.xfail]\n    derived = [*callbacks]\n"
        "    derived[0]('blocked')\n",
        "import pytest\ndef test_case():\n"
        "    callbacks = [pytest.xfail]\n    nested = {'group': callbacks}\n"
        "    nested['group'][0]('blocked')\n",
        "import pytest\ndef test_case():\n"
        "    callbacks = [pytest.xfail]\n    alias, = (callbacks,)\n"
        "    alias[0]('blocked')\n",
        "import pytest\ndef test_case():\n"
        "    callbacks = [pytest.xfail]\n    derived = list(item for item in callbacks)\n"
        "    derived[0]('blocked')\n",
    ),
)
def test_python_inventory_closes_aborting_container_derivations(source: str) -> None:
    try:
        declaration = guard.parse_python_declarations(
            "tests/test_example.py",
            source,
        )[0]
    except guard.TestCorpusGuardError:
        return
    assert declaration.ref != "tests/test_example.py::test_case"


def test_python_inventory_allows_direct_imported_data_in_command() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_example.py",
        "from sys import executable\n"
        "def test_case(run):\n"
        "    command = [executable, 'script.py']\n"
        "    run(command)\n",
    )

    assert len(declarations) == 1


@pytest.mark.parametrize(
    "instance_source",
    (
        "STOP = Stop()\n",
        "STOP = Stop()\nALIAS = STOP\n",
    ),
)
def test_python_inventory_closes_module_callable_instance_alias(
    instance_source: str,
) -> None:
    path = "tests/test_example.py"
    callback_name = "ALIAS" if "ALIAS" in instance_source else "STOP"
    active = (
        "class Stop:\n"
        "    def __call__(self, reason):\n        return None\n"
        f"{instance_source}"
        f"def test_case():\n    callbacks = [{callback_name}]\n"
        "    callbacks[0]('blocked')\n"
    )
    xfailed = active.replace(
        "        return None",
        "        import pytest\n        pytest.xfail(reason)",
    )

    try:
        active_ref = guard.parse_python_declarations(path, active)[0].ref
        xfailed_ref = guard.parse_python_declarations(path, xfailed)[0].ref
    except guard.TestCorpusGuardError:
        return
    assert active_ref != xfailed_ref


def test_python_inventory_closes_transitive_callable_instance_abort() -> None:
    path = "tests/test_example.py"
    active = (
        "class Stop:\n"
        "    def stop(self, reason):\n        return None\n"
        "    def __call__(self, reason):\n        self.stop(reason)\n"
        "STOP = Stop()\n"
        "def test_case():\n    callbacks = [STOP]\n    callbacks[0]('blocked')\n"
    )
    xfailed = active.replace(
        "        return None",
        "        import pytest\n        pytest.xfail(reason)",
    )

    assert len(guard.parse_python_declarations(path, active)) == 1
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic runtime helper container",
    ):
        guard.parse_python_declarations(path, xfailed)


@pytest.mark.parametrize(
    "body",
    (
        "    STOP()\n",
        "    callback = STOP\n    callback()\n",
    ),
)
def test_python_inventory_binds_direct_callable_instance_abort(body: str) -> None:
    path = "tests/test_example.py"
    active = (
        "class Stop:\n"
        "    def __call__(self):\n        return None\n"
        "STOP = Stop()\n"
        f"def test_case():\n{body}"
    )
    xfailed = active.replace(
        "        return None",
        "        import pytest\n        pytest.xfail('blocked')",
    )

    assert guard.parse_python_declarations(path, active)[0].ref != (
        guard.parse_python_declarations(path, xfailed)[0].ref
    )


def test_python_inventory_uses_final_callable_instance_binding() -> None:
    path = "tests/test_example.py"
    safe = (
        "import pytest\n"
        "class Stop:\n"
        "    def __call__(self):\n        pytest.xfail('stale')\n"
        "STOP = Stop()\n"
        "def safe():\n    return None\n"
        "STOP = safe\n"
        "def test_case():\n    callbacks = [STOP]\n    callbacks[0]()\n"
    )
    aborting = safe.replace(
        "def safe():\n    return None",
        "def safe():\n    pytest.xfail('current')",
    )

    safe_ref = guard.parse_python_declarations(path, safe)[0].ref
    try:
        aborting_ref = guard.parse_python_declarations(path, aborting)[0].ref
    except guard.TestCorpusGuardError:
        aborting_ref = "rejected"
    assert safe_ref != aborting_ref
    locally_safe = safe.replace(
        "def test_case():\n",
        "def test_case():\n    STOP = lambda: None\n",
    )
    assert len(guard.parse_python_declarations(path, locally_safe)) == 1


@pytest.mark.parametrize(
    "unpack",
    (
        "stop, = callbacks\n    stop()",
        "alias, = (callbacks,)\n    alias[0]()",
    ),
)
def test_python_inventory_allows_safe_static_callable_unpack(unpack: str) -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_example.py",
        "def stop():\n    return None\n"
        "def test_case():\n    callbacks = [stop]\n"
        f"    {unpack}\n",
    )

    assert len(declarations) == 1


def test_python_inventory_closes_aborting_named_container_unpack() -> None:
    source = (
        "import pytest\n"
        "def test_case():\n"
        "    callbacks = [pytest.xfail]\n"
        "    stop, = callbacks\n"
        "    stop('blocked')\n"
    )

    try:
        declaration = guard.parse_python_declarations(
            "tests/test_example.py",
            source,
        )[0]
    except guard.TestCorpusGuardError:
        return
    assert declaration.ref != "tests/test_example.py::test_case"


@pytest.mark.parametrize("local", (False, True))
def test_python_inventory_captures_callable_alias_at_assignment_time(
    local: bool,
) -> None:
    prefix = "import pytest\ndef safe():\n    return None\n"
    indent = "    " if local else ""
    opening = "def test_case():\n" if local else ""
    closing = "" if local else "def test_case():\n"
    aborting = (
        prefix
        + opening
        + f"{indent}STOP = pytest.xfail\n"
        + f"{indent}ALIAS = STOP\n"
        + f"{indent}STOP = safe\n"
        + closing
        + "    ALIAS('blocked')\n"
    )
    safe = (
        prefix
        + opening
        + f"{indent}STOP = safe\n"
        + f"{indent}ALIAS = STOP\n"
        + f"{indent}STOP = pytest.xfail\n"
        + closing
        + "    ALIAS('blocked')\n"
    )

    try:
        aborting_declaration = guard.parse_python_declarations(
            "tests/test_example.py",
            aborting,
        )[0]
    except guard.TestCorpusGuardError:
        aborting_declaration = None
    assert aborting_declaration is None or (
        aborting_declaration.ref != "tests/test_example.py::test_case"
    )
    safe_baseline = safe.replace(
        f"{indent}STOP = pytest.xfail\n",
        f"{indent}STOP = safe\n",
    )
    assert (
        guard.parse_python_declarations(
            "tests/test_example.py",
            safe,
        )[0].ref
        == guard.parse_python_declarations(
            "tests/test_example.py",
            safe_baseline,
        )[0].ref
    )


def test_python_inventory_keeps_captured_callable_instance_alias_authoritative() -> (
    None
):
    safe = (
        "import pytest\n"
        "class Stop:\n"
        "    def __call__(self):\n        return None\n"
        "STOP = Stop()\n"
        "ALIAS = STOP\n"
        "STOP = pytest.xfail\n"
        "def test_case():\n    ALIAS()\n"
    )
    aborting = safe.replace(
        "        return None",
        "        pytest.xfail('blocked')",
    )

    assert (
        guard.parse_python_declarations(
            "tests/test_example.py",
            safe,
        )[0].ref
        != guard.parse_python_declarations(
            "tests/test_example.py",
            aborting,
        )[0].ref
    )


@pytest.mark.parametrize(
    "derived",
    (
        "callbacks.copy()",
        "callbacks[:]",
        "list(callbacks)",
    ),
)
def test_python_inventory_rejects_derived_callable_container(
    derived: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic runtime helper container",
    ):
        guard.parse_python_declarations(
            "tests/test_example.py",
            "def stop(): return None\n"
            "def test_case():\n"
            "    callbacks = [stop]\n"
            f"    derived = {derived}\n"
            "    derived[0]()\n",
        )


@pytest.mark.parametrize(
    "dispatch",
    (
        "invoke(callbacks)",
        "callbacks.__getitem__(0)()",
        "operator.getitem(callbacks, 0)()",
    ),
)
def test_python_inventory_rejects_opaque_callable_container_dispatch(
    dispatch: str,
) -> None:
    imports = "import operator\n" if dispatch.startswith("operator") else ""
    helper = "def invoke(value): value[0]()\n" if dispatch.startswith("invoke") else ""
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic runtime helper container",
    ):
        guard.parse_python_declarations(
            "tests/test_example.py",
            imports
            + helper
            + "def stop(): return None\n"
            + "def test_case():\n"
            + "    callbacks = [stop]\n"
            + f"    {dispatch}\n",
        )


@pytest.mark.parametrize(
    "insertion",
    (
        "callbacks.append(pytest.xfail)",
        "callbacks[0] = pytest.xfail",
    ),
)
def test_python_inventory_rejects_callable_insertion_into_empty_container(
    insertion: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic runtime helper container",
    ):
        guard.parse_python_declarations(
            "tests/test_example.py",
            "import pytest\ndef test_case():\n"
            "    callbacks = []\n"
            f"    {insertion}\n"
            "    callbacks[0]()\n",
        )


def test_python_inventory_binds_closure_static_callable_container_target() -> None:
    path = "tests/test_example.py"

    def ref_for(helper_body: str) -> str:
        return guard.parse_python_declarations(
            path,
            f"def stop():\n    {helper_body}\n"
            "def test_case():\n"
            "    callbacks = (stop,)\n"
            "    def run():\n"
            "        callbacks[0]()\n"
            "    run()\n",
        )[0].ref

    assert ref_for("return None") != ref_for(
        "import pytest\n    pytest.xfail('disabled')"
    )


@pytest.mark.parametrize(
    "source",
    (
        "import pytest\nCALLBACKS = (pytest.xfail,)\n"
        "def test_case():\n    CALLBACKS[0]('disabled')\n",
        "from tests.helper import CALLBACKS\n"
        "def test_case():\n    CALLBACKS[0]('disabled')\n",
    ),
)
def test_python_inventory_rejects_opaque_nonlocal_callable_container(
    source: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic runtime helper container",
    ):
        guard.parse_python_declarations("tests/test_example.py", source)


def test_python_inventory_rejects_dynamic_callable_container_target() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic runtime helper container",
    ):
        guard.parse_python_declarations(
            "tests/test_example.py",
            "def stop():\n    return None\ndef test_case(index):\n"
            "    callbacks = [stop]\n    callbacks[index]()\n",
        )


def test_python_inventory_ignores_non_disabling_imported_runtime_helper_change() -> (
    None
):
    test_source = "from tests.helper import prepare\ndef test_case():\n    prepare()\n"

    def ref_for(value: object) -> str:
        resolver = guard._python_import_resolver(
            lambda path: (
                f"def prepare():\n    return {value!r}\n"
                if path == "tests/helper.py"
                else None
            )
        )
        return guard._python_inventory_entries(
            "tests/test_example.py", test_source, resolver
        )[0][0].ref

    assert ref_for(1) == ref_for(2)
    assert ref_for("runtime-abort-posture=true") == ref_for(
        "runtime-abort-posture=false"
    )


def test_python_inventory_binds_module_qualified_runtime_abort_helper() -> None:
    test_source = (
        "import tests.helper as helper\ndef test_case():\n    helper.prepare()\n"
    )

    def ref_for(helper_source: str) -> str:
        resolver = guard._python_import_resolver(
            lambda path: helper_source if path == "tests/helper.py" else None
        )
        return guard._python_inventory_entries(
            "tests/test_example.py", test_source, resolver
        )[0][0].ref

    assert ref_for("def prepare():\n    return None\n") != ref_for(
        "import pytest\ndef prepare():\n    pytest.xfail('disabled')\n"
    )


def test_python_inventory_binds_member_before_imported_instance_method() -> None:
    test_source = (
        "import tests.helper as helper\ndef test_case():\n    helper.VALUE.as_posix()\n"
    )

    def ref_for(value: str) -> str:
        resolver = guard._python_import_resolver(
            lambda path: (
                "from pathlib import Path\n"
                f"VALUE = Path({value!r})\n"
                "import pytest\n"
                "def as_posix():\n"
                "    pytest.xfail('unrelated')\n"
                if path == "tests/helper.py"
                else None
            )
        )
        return guard._python_inventory_entries(
            "tests/test_example.py", test_source, resolver
        )[0][0].ref

    # The receiver value changes execution data, not execution-disabling posture.
    assert ref_for("one") == ref_for("two")


@pytest.mark.parametrize(
    "import_source",
    (
        "import tests\n",
        "import tests.helper\n",
    ),
)
def test_python_inventory_binds_package_qualified_runtime_helper(
    import_source: str,
) -> None:
    test_source = import_source + "def test_case():\n    tests.helper.stop()\n"

    def ref_for(body: str) -> str:
        sources = {
            "tests/__init__.py": "from . import helper\n",
            "tests/helper.py": f"def stop():\n    {body}\n",
        }
        resolver = guard._python_import_resolver(sources.get)
        return guard._python_inventory_entries(
            "tests/test_example.py", test_source, resolver
        )[0][0].ref

    assert ref_for("return None") != ref_for("import pytest; pytest.xfail('disabled')")


def test_python_inventory_prefers_static_package_member_over_dormant_module() -> None:
    test_source = "import tests\ndef test_case():\n    tests.helper.stop()\n"

    def ref_for(body: str, dormant_body: str) -> str:
        sources = {
            "tests/__init__.py": (
                "class Runner:\n"
                f"    def stop(self):\n        {body}\n"
                "helper = Runner()\n"
            ),
            "tests/helper.py": f"def stop():\n    {dormant_body}\n",
        }
        resolver = guard._python_import_resolver(sources.get)
        return guard._python_inventory_entries(
            "tests/test_example.py", test_source, resolver
        )[0][0].ref

    active = ref_for("return None", "return None")
    assert active != ref_for(
        "import pytest; pytest.xfail('disabled')",
        "return None",
    )
    assert active == ref_for(
        "return None",
        "import pytest; pytest.xfail('dormant')",
    )


def test_python_inventory_binds_package_initializer_explicit_submodule() -> None:
    test_source = "import tests\ndef test_case():\n    tests.helper.stop()\n"

    def ref_for(body: str) -> str:
        sources = {
            "tests/__init__.py": "import tests.helper\n",
            "tests/helper.py": f"def stop():\n    {body}\n",
        }
        resolver = guard._python_import_resolver(sources.get)
        return guard._python_inventory_entries(
            "tests/test_example.py", test_source, resolver
        )[0][0].ref

    assert ref_for("return None") != ref_for("import pytest; pytest.xfail('disabled')")


def test_python_inventory_binds_aliased_direct_import_original_member() -> None:
    test_source = "from tests.helper import stop as s\ndef test_case():\n    s()\n"

    def ref_for(abort_body: str) -> str:
        sources = {
            "tests/helper.py": (
                "from tests.abort import stop as abort\ndef stop():\n    abort()\n"
            ),
            "tests/abort.py": f"def stop():\n    {abort_body}\n",
        }
        resolver = guard._python_import_resolver(sources.get)
        return guard._python_inventory_entries(
            "tests/test_example.py", test_source, resolver
        )[0][0].ref

    assert ref_for("return None") != ref_for("import pytest; pytest.xfail('disabled')")


@pytest.mark.parametrize(
    "test_source",
    (
        "def prepare():\n    return 1\ndef test_case():\n"
        "    alias = prepare\n    alias()\n",
        "class TestExample:\n    def prepare(self):\n        return 1\n"
        "    def test_case(self):\n        self.prepare()\n",
    ),
)
def test_python_inventory_binds_aliased_local_runtime_helper(
    test_source: str,
) -> None:
    before = guard.parse_python_declarations("tests/test_example.py", test_source)[
        0
    ].ref
    after = guard.parse_python_declarations(
        "tests/test_example.py", test_source.replace("return 1", "return 2")
    )[0].ref

    assert before != after


def test_python_inventory_binds_conditional_pytest_namespace_alias() -> None:
    def refs_for(enabled: bool) -> tuple[str, ...]:
        return tuple(
            declaration.ref
            for declaration in guard.parse_python_declarations(
                "tests/test_sample.py",
                "import pytest\n"
                f"ENABLED = {enabled!r}\n"
                "if ENABLED:\n"
                "    q = pytest\n"
                "@q.fixture(autouse=True)\n"
                "def environment():\n"
                "    return None\n"
                "def test_case(): pass\n",
            )
        )

    assert refs_for(False) != refs_for(True)


@pytest.mark.parametrize(
    "source",
    (
        "import pytest\nattr = getattr\n"
        "attr(pytest, 'skip')('disabled', allow_module_level=True)\n",
        "import builtins\nimport pytest\nattr = builtins.getattr\n"
        "attr(pytest, 'skip')('disabled', allow_module_level=True)\n",
        "import pytest\n(attr,) = (getattr,)\n"
        "attr(pytest, 'skip')('disabled', allow_module_level=True)\n",
        "import pytest\nif True:\n    q = pytest\n"
        "q.skip('disabled', allow_module_level=True)\n",
    ),
)
def test_python_inventory_rejects_indirect_module_pytest_skip(source: str) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="module-level pytest collection abort",
    ):
        guard.parse_python_declarations("tests/test_sample.py", source)


def test_python_inventory_rejects_walrus_unittest_case_abort() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="module-level unittest collection abort",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "import unittest\nraise (uc := unittest.case).SkipTest('disabled')\n",
        )


@pytest.mark.parametrize(
    "binding",
    (
        "def provide(name): return None\n__getattr__ = provide\n",
        "from helpers import provide as __getattr__\n",
        "import helpers as __getattr__\n",
    ),
)
def test_python_inventory_rejects_assigned_module_getattr(binding: str) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic module attributes",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            binding + "def test_case(): pass\n",
        )


def test_python_inventory_reenables_deleted_function_test_attribute() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        "def test_case(): pass\ntest_case.__test__ = False\ndel test_case.__test__\n",
    )

    assert [item.ref for item in declarations] == ["tests/test_sample.py::test_case"]


def test_python_inventory_rejects_dynamic_function_alias_test_mutation() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic Python function __test__ mutation",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "def test_case(): pass\n"
            "Alias = identity(test_case)\n"
            "Alias.__test__ = False\n",
        )


def test_python_inventory_does_not_reuse_rebound_function_alias() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        "def test_case(): pass\n"
        "Alias = test_case\n"
        "Alias = object()\n"
        "Alias.__test__ = False\n",
    )

    assert [item.ref for item in declarations] == ["tests/test_sample.py::test_case"]


def test_python_inventory_rejects_unresolved_parametrize_alias() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="parametrize decorator cannot be resolved",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            """
@custom_parametrize("value", ["one"])
def test_case(value):
    pass
""",
        )


@pytest.mark.parametrize(
    "decorator",
    ("custom_parametrize", "pytest.mark.parametrize", "parametrize_alias"),
)
def test_python_inventory_rejects_bare_parametrize_decorators(
    decorator: str,
) -> None:
    imports = "import pytest\n"
    if decorator == "parametrize_alias":
        imports += "parametrize_alias = pytest.mark.parametrize\n"
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="parametrize decorator cannot be resolved",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            f"{imports}@{decorator}\ndef test_case(value): pass\n",
        )


@pytest.mark.parametrize(
    "rebind",
    (
        "mark = object()",
        "mark.disable = lambda function: None",
    ),
)
def test_python_inventory_rejects_rebound_imported_pytest_mark(
    rebind: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="Python test decorator",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "from pytest import mark\n"
            f"{rebind}\n"
            "@mark.disable\n"
            "def test_case(): pass\n",
        )


def test_python_inventory_rejects_tests_inside_module_control_flow() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="module control flow",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            """
if True:
    def test_conditional():
        pass
""",
        )


@pytest.mark.parametrize(
    ("source", "message"),
    (
        (
            "class TestOriginal:\n    def test_case(self): pass\n"
            "TestAlias = TestOriginal\n",
            "test-class assignment",
        ),
        (
            'def test_case(): pass\nglobals()["test_case"] = None\n',
            "indirect Python test-name rebinding",
        ),
        (
            "def test_case(): pass\nname = get_name()\nglobals()[name] = None\n",
            "indirect Python test-name rebinding",
        ),
        (
            "class TestGroup:\n    if enabled:\n        def test_case(self): pass\n",
            "class control flow",
        ),
        (
            "import pytest\n"
            "p = pytest.mark.parametrize\n"
            'pytestmark = p("value", [1, 2])\n'
            "def test_case(value): pass\n",
            "module-level pytestmark parametrization",
        ),
        (
            "import pytest\n"
            "def test_case(value): pass\n"
            'pytest.mark.parametrize("value", [1, 2])(test_case)\n',
            "post-definition Python parametrization",
        ),
        (
            "import pytest\n"
            "def test_case(): pass\n"
            "pytest.mark.skip(test_case)\n",
            "post-definition Python execution mark",
        ),
        (
            "import pytest\n"
            "def test_case(): pass\n"
            "pytest.mark.skipif(test_case)\n",
            "post-definition Python execution mark",
        ),
        (
            "import pytest\n"
            "def test_case(): pass\n"
            "pytest.mark.xfail(test_case)\n",
            "post-definition Python execution mark",
        ),
        (
            "from pytest import mark\n"
            "def test_case(): pass\n"
            'mark.skip(reason="retired")(test_case)\n',
            "post-definition Python execution mark",
        ),
        (
            "from pytest import mark\n"
            "execution_mark = mark\n"
            "def test_case(): pass\n"
            'execution_mark.xfail(reason="retired")(test_case)\n',
            "post-definition Python execution mark",
        ),
        (
            "def disable(function): function.__test__ = False\n"
            "def test_case(): pass\n"
            "disable(test_case)\n",
            "dynamic Python function __test__ mutation",
        ),
        (
            "def disable(function): function.__test__ = False\n"
            "def test_case(): pass\n"
            "mask = disable\n"
            "mask(test_case)\n",
            "dynamic Python function __test__ mutation",
        ),
        (
            "import pytest\n"
            "import unittest\n"
            "class Cases(unittest.TestCase):\n"
            "    def test_case(self): pass\n"
            'pytest.mark.skip(reason="retired")(Cases)\n',
            "post-definition Python execution mark",
        ),
        (
            "import pytest\n"
            "def value(): return 1\n"
            "value = pytest.fixture(params=[1, 2])(value)\n"
            "def test_case(value): assert value\n",
            "parameterized Python fixtures",
        ),
        (
            'def test_case(): pass\nglobals().update({"test_case": None})\n',
            "indirect Python test-name rebinding",
        ),
        (
            'def test_case(): pass\nglobals().pop("test_case")\n',
            "indirect Python test-name rebinding",
        ),
        (
            'def test_case(): pass\nlocals().pop("test_case")\n',
            "indirect Python test-name rebinding",
        ),
        (
            'def test_case(): pass\nvars().update({"test_case": None})\n',
            "indirect Python test-name rebinding",
        ),
        (
            'def test_case(): pass\nnamespace = globals()\nnamespace.pop("test_case")\n',
            "indirect Python test-name rebinding",
        ),
        (
            'def test_case(): pass\nnamespace = globals()\nnamespace["test_case"] = None\n',
            "indirect Python test-name rebinding",
        ),
        (
            'def test_case(): pass\n(namespace := globals()).pop("test_case")\n',
            "indirect Python test-name rebinding",
        ),
        (
            "import pytest\n"
            "def test_case(value): pass\n"
            "alias = test_case\n"
            'pytest.mark.parametrize("value", [1, 2])(alias)\n',
            "post-definition Python parametrization",
        ),
        (
            "import pytest\n"
            "def test_case(value): pass\n"
            "alias = test_case\n"
            'pytest.mark.parametrize("value", [1, 2])(alias)\n'
            "alias = object\n",
            "post-definition Python parametrization",
        ),
        (
            "def helper(self): pass\n"
            "class TestGroup:\n"
            "    if enabled:\n"
            "        test_case = helper\n",
            "class control flow",
        ),
        (
            "class RemoveTests(type): pass\n"
            "class TestGroup(metaclass=RemoveTests):\n"
            "    def test_case(self): pass\n",
            "test class metaclass",
        ),
        (
            "def disable(function): return None\n@disable\ndef test_case(): pass\n",
            "test decorator",
        ),
        (
            "pytest = build_fake_pytest()\n"
            "@pytest.mark.disable\n"
            "def test_case(): pass\n",
            "test decorator",
        ),
        (
            "import pytest\n"
            "class TestGroup:\n"
            '    pytestmark = pytest.mark.parametrize("value", [1, 2])\n'
            "    def test_case(self, value): pass\n",
            "class-level pytestmark parametrization",
        ),
        (
            "import pytest\n"
            "pytestmark = []\n"
            'pytestmark.append(pytest.mark.parametrize("value", [1, 2]))\n'
            "def test_case(value): pass\n",
            "dynamic pytestmark mutation",
        ),
        (
            "import pytest\n"
            "pytestmark = []\n"
            "marks = pytestmark\n"
            'marks.append(pytest.mark.parametrize("value", [1, 2]))\n'
            "def test_case(value): pass\n",
            "dynamic pytestmark mutation",
        ),
        (
            "import pytest\n"
            "pytestmark = marks = []\n"
            'marks.append(pytest.mark.parametrize("value", [1, 2]))\n'
            "def test_case(value): pass\n",
            "dynamic pytestmark mutation",
        ),
        (
            "import pytest\n"
            "class TestGroup:\n"
            "    pytestmark = []\n"
            '    pytestmark += [pytest.mark.parametrize("value", [1, 2])]\n'
            "    def test_case(self, value): pass\n",
            "dynamic pytestmark mutation",
        ),
        (
            "class RemoveTests(type): pass\n"
            "class Base(metaclass=RemoveTests): pass\n"
            "class TestGroup(Base):\n"
            "    def test_case(self): pass\n",
            "test class metaclass",
        ),
        (
            "class Base:\n"
            "    def test_inherited(self): pass\n"
            "Base.__test__ = False\n"
            "class TestGroup(Base): pass\n",
            "post-definition Python class __test__ mutation",
        ),
        (
            "class TestGroup:\n"
            "    def test_case(self): pass\n"
            "Alias = TestGroup\n"
            "Alias.__init__ = lambda self: None\n",
            "post-definition Python class constructor mutation",
        ),
        (
            "class TestGroup:\n"
            "    def test_case(self): pass\n"
            "(Alias := TestGroup).__init__ = lambda self: None\n",
            "post-definition Python class constructor mutation",
        ),
        (
            "class TestGroup:\n"
            "    def test_case(self): pass\n"
            "(TestGroup if True else object).__init__ = lambda self: None\n",
            "post-definition Python class constructor mutation",
        ),
        (
            "class TestGroup:\n"
            "    def test_case(self): pass\n"
            "setattr(TestGroup, '__init__', lambda self: None)\n",
            "post-definition Python class constructor mutation",
        ),
        (
            "class TestGroup: pass\nTestGroup.test_case = lambda self: None\n",
            "post-definition Python test method mutation",
        ),
        (
            "class TestGroup: pass\n"
            "setattr(TestGroup, 'test_case', lambda self: None)\n",
            "post-definition Python test method mutation",
        ),
        (
            "class TestGroup:\n"
            "    def test_case(self): pass\n"
            "TestGroup.__unittest_skip__ = True\n",
            "post-definition unittest skip mutation",
        ),
        (
            "class TestGroup:\n"
            "    def test_case(self): pass\n"
            "setattr(TestGroup.test_case, '__unittest_skip__', True)\n",
            "post-definition unittest skip mutation",
        ),
        (
            "class TestGroup:\n"
            "    def test_case(self): pass\n"
            "type.__setattr__(TestGroup.test_case, '__unittest_skip__', True)\n",
            "post-definition unittest skip mutation",
        ),
        (
            "class TestGroup:\n"
            "    def test_case(self): pass\n"
            "TestGroup.test_case.__dict__['__unittest_skip__'] = True\n",
            "post-definition unittest skip mutation",
        ),
        (
            "class TestGroup:\n"
            "    def test_case(self): pass\n"
            "vars(TestGroup.test_case)['__unittest_skip__'] = True\n",
            "post-definition unittest skip mutation",
        ),
        (
            "class TestGroup:\n"
            "    def test_case(self): pass\n"
            "vars(TestGroup.test_case).update({'__unittest_skip__': True})\n",
            "post-definition unittest skip mutation",
        ),
        (
            "def test_case(): pass\nsetattr(test_case, '__test__', False)\n",
            "function __test__ mutation",
        ),
        (
            "def test_case(): pass\n"
            "alias = test_case\n"
            "setattr(alias, '__test__', False)\n",
            "function __test__ mutation",
        ),
        (
            "def test_case(): pass\nsetattr((alias := test_case), '__test__', False)\n",
            "function __test__ mutation",
        ),
        (
            "def test_case(): pass\n"
            "(alias,) = (test_case,)\n"
            "setattr(alias, '__test__', False)\n",
            "function __test__ mutation",
        ),
        (
            "class Base:\n"
            "    def test_inherited(self): pass\n"
            "Base.__new__ = lambda cls: object.__new__(cls)\n"
            "class TestGroup(Base): pass\n",
            "post-definition Python class constructor mutation",
        ),
        (
            "class Base:\n"
            "    def test_inherited(self): pass\n"
            "Alias = Base\n"
            "Alias.__test__ = False\n"
            "class TestGroup(Base): pass\n",
            "post-definition Python class __test__ mutation",
        ),
        (
            "class Base:\n"
            "    def test_inherited(self): pass\n"
            "(Alias,) = (Base,)\n"
            "Alias.__test__ = False\n"
            "class TestGroup(Base): pass\n",
            "post-definition Python class __test__ mutation",
        ),
        (
            "import unittest\n"
            "Case = unittest.TestCase\n"
            "class Helper:\n"
            "    global Case\n"
            "    Case = object\n"
            "class WidgetCases(Case):\n"
            "    def test_widget(self): pass\n",
            "unittest.TestCase alias",
        ),
        (
            "import unittest\n"
            "unittest = Fake\n"
            "class WidgetCases(unittest.TestCase):\n"
            "    def test_widget(self): pass\n",
            "unittest module alias",
        ),
        (
            "import unittest as u\n"
            "Original = u.TestCase\n"
            "u.TestCase = object\n"
            "class WidgetCases(u.TestCase):\n"
            "    def test_widget(self): pass\n"
            "u.TestCase = Original\n",
            "unittest.TestCase attribute",
        ),
        (
            "import unittest as u\n"
            "alias = u\n"
            "alias.TestCase = object\n"
            "class WidgetCases(u.TestCase):\n"
            "    def test_widget(self): pass\n",
            "unittest.TestCase attribute",
        ),
        (
            "import unittest as u\n"
            "alias = u\n"
            "setattr(alias, 'TestCase', object)\n"
            "class WidgetCases(u.TestCase):\n"
            "    def test_widget(self): pass\n",
            "unittest.TestCase attribute",
        ),
        (
            "import pytest as p\np = helpers\n@p.fixture\ndef test_case(): pass\n",
            "pytest fixture alias",
        ),
        (
            "import pytest as p\n"
            "original = p.fixture\n"
            "p.fixture = lambda function: function\n"
            "@p.fixture\n"
            "def test_case(): pass\n"
            "p.fixture = original\n",
            "pytest fixture alias",
        ),
        (
            "import pytest as p\n"
            "alias = p\n"
            "setattr(alias, 'fixture', lambda function: function)\n"
            "@p.fixture\n"
            "def test_case(): pass\n",
            "pytest fixture alias",
        ),
        (
            "from pytest import fixture as fx\n"
            "fx = helpers.fixture\n"
            "@fx\n"
            "def test_case(): pass\n",
            "pytest fixture alias",
        ),
        (
            "def test_case(): pass\nlocals()['test_case'] = None\n",
            "indirect Python test-name rebinding",
        ),
        (
            "def test_case(): pass\nvars()['test_case'] = None\n",
            "indirect Python test-name rebinding",
        ),
        (
            "def test_case(): pass\n"
            "namespace = locals()\n"
            "namespace['test_case'] = None\n",
            "indirect Python test-name rebinding",
        ),
        (
            "def test_case(): pass\n"
            "namespace = vars()\n"
            "namespace['test_case'] = None\n",
            "indirect Python test-name rebinding",
        ),
        (
            "def test_case(): pass\n"
            "test_case.__test__ = False\n"
            "if enabled:\n    del test_case.__test__\n",
            "__test__ mutation inside module control flow",
        ),
        (
            "def test_case(): pass\nif enabled:\n    test_case.__test__ += True\n",
            "__test__ mutation inside module control flow",
        ),
        (
            "@helpers.fixture\ndef test_case(): pass\n",
            "test decorator",
        ),
        (
            "import unittest\n"
            "Case = unittest.TestCase\n"
            "class Helper:\n"
            "    globals()['Case'] = object\n"
            "class WidgetCases(Case):\n"
            "    def test_widget(self): pass\n",
            "unittest.TestCase alias",
        ),
    ),
)
def test_python_inventory_rejects_dynamic_collection_rebinding(
    source: str,
    message: str,
) -> None:
    with pytest.raises(guard.TestCorpusGuardError, match=message):
        guard.parse_python_declarations("tests/test_sample.py", source)


def test_python_inventory_allows_shadowed_imported_mark_name() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        "from pytest import mark\n"
        "class mark:\n"
        "    @staticmethod\n"
        "    def skip(function): return function\n"
        "def test_case(): pass\n"
        "mark.skip(test_case)\n",
    )

    assert [item.ref for item in declarations] == ["tests/test_sample.py::test_case"]


def test_python_inventory_rejects_destructured_imported_mark_alias() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="post-definition Python execution mark",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "from pytest import mark\n"
            "def test_case(): pass\n"
            "mark, unused = (mark, 1)\n"
            "mark.skip(test_case)\n",
        )


def test_python_inventory_allows_mark_on_non_test_unittest_member() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        "import pytest\n"
        "import unittest\n"
        "class Cases(unittest.TestCase):\n"
        "    def helper(self): pass\n"
        "    def test_case(self): pass\n"
        "pytest.mark.skip(Cases.helper)\n",
    )

    assert [item.ref for item in declarations] == [
        "tests/test_sample.py::Cases::test_case"
    ]


def test_python_inventory_rejects_mark_on_unittest_test_member() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="post-definition Python execution mark",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "import pytest\n"
            "import unittest\n"
            "class Cases(unittest.TestCase):\n"
            "    def test_case(self): pass\n"
            "pytest.mark.skip(Cases.test_case)\n",
        )


def test_python_inventory_rejects_mark_on_inherited_test_member() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="post-definition Python execution mark",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "import pytest\n"
            "class TestBase:\n"
            "    def test_inherited(self): pass\n"
            "class TestChild(TestBase): pass\n"
            "pytest.mark.skip(TestChild.test_inherited)\n",
        )


@pytest.mark.parametrize(
    "function_body",
    (
        "namespace = locals()\n    namespace['value'] = 1",
        "namespace = vars()\n    namespace['value'] = 1",
        "locals().pop('value', None)",
        "vars().update({'value': 1})",
    ),
)
def test_python_inventory_allows_function_local_namespace_mutation(
    function_body: str,
) -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        f"def test_case():\n    {function_body}\n",
    )

    assert [item.ref for item in declarations] == ["tests/test_sample.py::test_case"]


def test_python_source_ref_hashes_only_the_replacement_declaration() -> None:
    test_ref = "tests/test_sample.py::test_replacement"
    before = """
import first_dependency

def test_replacement():
    assert True

def test_neighbor():
    assert True
"""
    unrelated_change = """
import second_dependency

def test_replacement():
    assert True

def test_neighbor():
    assert False
"""
    replacement_change = unrelated_change.replace("assert True", "assert 1 == 1", 1)

    source_ref = guard._source_ref_from_text(test_ref, before)
    assert guard._source_ref_from_text(test_ref, unrelated_change) == source_ref
    assert guard._source_ref_from_text(test_ref, replacement_change) != source_ref


def test_frontend_inventory_preserves_runtime_titles_and_disambiguates_duplicates() -> (
    None
):
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        """
test("renders   a panel", () => {});
it.only('renders a panel', () => {});
it('renders a panel', () => {});
test.skip(`blocks mutation`, () => {});
""",
    )

    refs = [item.ref for item in declarations]
    assert refs[:3] == [
        "apps/control-center/src/example.test.tsx::renders   a panel",
        "apps/control-center/src/example.test.tsx::renders a panel",
        "apps/control-center/src/example.test.tsx::renders a panel#2",
    ]
    assert refs[3].startswith(
        "apps/control-center/src/example.test.tsx::blocks mutation"
        "::execution-disabled:skip::identity-sha256:"
    )


@pytest.mark.parametrize(
    "shadowing_source",
    [
        'const test = helper; test("not collected", () => {});',
        'function it() {} it("not collected", () => {});',
        'const { test } = helper; test("not collected", () => {});',
        'const [test] = helper; test("not collected", () => {});',
        'const helper = (test) => test("not collected", () => {});',
        'import { test } from "local-helper"; test("not collected", () => {});',
    ],
)
def test_frontend_inventory_rejects_shadowed_runner_names(
    shadowing_source: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="frontend test API name is shadowed",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            shadowing_source,
        )


@pytest.mark.parametrize(
    "source",
    (
        'test?.("case", () => {});\n',
        'describe?.("suite", () => { test("case", () => {}); });\n',
    ),
)
def test_frontend_inventory_rejects_optional_runner_calls(source: str) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="frontend optional .* API call",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            source,
        )


@pytest.mark.parametrize(
    "source",
    (
        '(globalThis as any).test = () => undefined;\ntest("case", () => {});\n',
        'globalThis["test"] = () => undefined;\ntest("case", () => {});\n',
        "globalThis.describe = () => undefined;\n"
        'describe("suite", () => { test("case", () => {}); });\n',
        "(globalThis as any)['describe'] = () => undefined;\n"
        'describe("suite", () => { test("case", () => {}); });\n',
    ),
)
def test_frontend_inventory_rejects_global_runner_mutation(source: str) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="frontend global .* API mutation",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            source,
        )


@pytest.mark.parametrize(
    "source",
    (
        'Object.defineProperty(globalThis, "test", { value: () => undefined });\n'
        'test("case", () => {});\n',
        'Reflect.defineProperty(globalThis, "test", { value: () => undefined });\n'
        'test("case", () => {});\n',
        'Reflect.set(globalThis, "describe", () => undefined);\n'
        'describe("suite", () => { test("case", () => {}); });\n',
        "Object.assign(globalThis, { test: () => undefined });\n"
        'test("case", () => {});\n',
    ),
)
def test_frontend_inventory_rejects_global_runner_property_mutation(
    source: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="frontend global .* API mutation",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            source,
        )


def test_frontend_inventory_allows_nonshadowing_property_destructure() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.ts",
        """
import { it } from "vitest";
const { test: helperTest } = helper;
it("collected", () => helperTest());
""",
    )

    assert [declaration.ref for declaration in declarations] == [
        "apps/control-center/src/example.test.ts::collected"
    ]


def test_frontend_source_ref_hashes_only_the_replacement_declaration() -> None:
    path = "apps/control-center/src/example.test.ts"
    test_ref = f"{path}::replacement"
    before = """
import { it } from "vitest";
const unrelated = "first";
it("replacement", () => { expect(true).toBe(true); });
it("neighbor", () => { expect(true).toBe(true); });
"""
    unrelated_change = """
import { it } from "vitest";
const unrelated = "second";
it("replacement", () => { expect(true).toBe(true); });
it("neighbor", () => { expect(false).toBe(true); });
"""
    replacement_change = unrelated_change.replace(
        "expect(true).toBe(true)",
        "expect(1).toBe(1)",
        1,
    )

    source_ref = guard._source_ref_from_text(test_ref, before)
    assert guard._source_ref_from_text(test_ref, unrelated_change) == source_ref
    assert guard._source_ref_from_text(test_ref, replacement_change) != source_ref


def test_frontend_inventory_includes_parameterized_test_titles() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        """
const cases = [["bound"]] as const;
it.each([
  ["one", { nested: call("value)") }],
  ["two", { nested: true }],
])("renders %s safely", () => {});
test.concurrent.each(cases)("rejects %s", () => {});
test.for(cases)("binds one case object", () => {});
test.each`
  name | allowed
  ${"x"} | ${false}
`("blocks $name", () => {});
""",
    )

    assert [item.ref.split("::parameters-sha256:", 1)[0] for item in declarations] == [
        "apps/control-center/src/example.test.tsx::renders %s safely",
        "apps/control-center/src/example.test.tsx::rejects %s",
        "apps/control-center/src/example.test.tsx::binds one case object",
        "apps/control-center/src/example.test.tsx::blocks $name",
    ]
    assert all("::parameters-sha256:" in item.ref for item in declarations)


def test_frontend_inventory_binds_parameter_rows_to_stable_refs() -> None:
    path = "apps/control-center/src/example.test.tsx"
    before = guard.parse_frontend_declarations(
        path,
        'test.each([["one"], ["two"]])("renders %s", () => {});',
    )
    after = guard.parse_frontend_declarations(
        path,
        'test.each([["one"]])("renders %s", () => {});',
    )

    assert before[0].ref != after[0].ref


def test_frontend_inventory_binds_identifier_initializer_to_stable_ref() -> None:
    path = "apps/control-center/src/example.test.tsx"
    before = guard.parse_frontend_declarations(
        path,
        """
const cases: ReadonlyArray<readonly [string]> = [["one"], ["two"]];
test.each(cases)("renders %s", () => {});
""",
    )
    after = guard.parse_frontend_declarations(
        path,
        """
const cases: ReadonlyArray<readonly [string]> = [["one"]];
test.each(cases)("renders %s", () => {});
""",
    )

    assert before[0].ref != after[0].ref


def test_frontend_inventory_rejects_unresolved_parameter_identifier() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="binding cannot be resolved safely",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            'test.each(cases)("renders %s", () => {});',
        )


def test_frontend_inventory_rejects_mutated_parameter_identifier() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="binding is mutated before collection",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            """
const cases = [["one"]];
cases.push(["two"]);
test.each(cases)("renders %s", () => {});
""",
        )


def test_frontend_inventory_rejects_helper_mediated_parameter_mutation() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="passed to an unproven call before collection",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            """
const cases = [["one"], ["two"]];
removeLast(cases);
test.each(cases)("renders %s", () => {});
""",
        )


def test_frontend_inventory_rejects_alias_mediated_parameter_mutation() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="binding has an unproven use before collection",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            """
const cases = [["one"], ["two"]];
const alias = cases;
alias.pop();
test.each(cases)("renders %s", () => {});
""",
        )


def test_frontend_inventory_rejects_predeclared_closure_mutation() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="used by an unproven helper",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            """
function trim() { cases.pop(); }
const cases = [["one"], ["two"]];
trim();
test.each(cases)("renders %s", () => {});
""",
        )


def test_frontend_inventory_rejects_executable_typeof_mutation() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="binding has an unproven use before collection",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            """
const cases = [["one"], ["two"]];
typeof cases["pop"]();
test.each(cases)("renders %s", () => {});
""",
        )


def test_frontend_inventory_rejects_executable_typeof_after_type_query() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="binding is mutated before collection",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            """
const cases = [["one"], ["two"]];
const typed: typeof cases = typeof cases["pop"]();
test.each(cases)("renders %s", () => {});
""",
        )


def test_frontend_inventory_supports_semicolonless_parameter_binding() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        """
const cases = [["one"]]
test.each(cases)("renders %s", () => {})
""",
    )

    assert len(declarations) == 1


def test_frontend_inventory_binds_parameter_initializer_dependencies() -> None:
    path = "apps/control-center/src/example.test.tsx"
    before = guard.parse_frontend_declarations(
        path,
        """
const base = [["one"], ["two"]];
const cases = [...base] as const;
test.each(cases)("renders %s", () => {});
""",
    )
    after = guard.parse_frontend_declarations(
        path,
        """
const base = [["one"]];
const cases = [...base] as const;
test.each(cases)("renders %s", () => {});
""",
    )

    assert before[0].ref != after[0].ref


def test_frontend_inventory_resolves_wrapped_parameter_identifier() -> None:
    path = "apps/control-center/src/example.test.tsx"
    before = guard.parse_frontend_declarations(
        path,
        """
const cases = [["one"], ["two"]];
test.each((cases))("renders %s", () => {});
""",
    )
    after = guard.parse_frontend_declarations(
        path,
        """
const cases = [["one"]];
test.each((cases))("renders %s", () => {});
""",
    )

    assert before[0].ref != after[0].ref


def test_frontend_inventory_allows_runtime_reads_in_prior_parameter_callback() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        """
const cases = [["one"]];
test.each(cases)("first %s", () => {
  expect(cases).toHaveLength(1);
});
test.each(cases)("second %s", () => {});
""",
    )

    assert len(declarations) == 2


def test_frontend_parameter_binding_ignores_unrelated_initializer_changes() -> None:
    path = "apps/control-center/src/example.test.tsx"
    before = guard.parse_frontend_declarations(
        path,
        """
const unrelated = "before";
const cases = [["one"]];
test.each(cases)("renders %s", () => unrelated);
""",
    )
    after = guard.parse_frontend_declarations(
        path,
        """
const unrelated = "after";
const cases = [["one"]];
test.each(cases)("renders %s", () => unrelated);
""",
    )

    assert before[0].ref == after[0].ref


def test_frontend_inventory_binds_relative_imported_initializer(
    tmp_path: Path,
) -> None:
    test_path = "apps/control-center/src/example.test.ts"
    source_path = tmp_path / "apps/control-center/src/cases.ts"
    source_path.parent.mkdir(parents=True)
    source_path.write_text('export const CASES = [["one"], ["two"]] as const;\n')
    test_text = """
import { CASES } from "./cases";
test.each(CASES)("renders %s", () => {});
"""

    before = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)
    source_path.write_text('export const CASES = [["one"]] as const;\n')
    after = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)

    assert before[0].ref != after[0].ref


def test_frontend_inventory_assigns_duplicates_in_source_order() -> None:
    path = "apps/control-center/src/example.test.tsx"
    declarations = guard.parse_frontend_declarations(
        path,
        """
const enabled = true;
test.runIf(enabled)("same", () => {});
test("same", () => {});
test("alpha", () => {});
test("alpha", () => {});
""",
    )

    refs = [item.ref for item in declarations]
    assert refs[0].startswith(f"{path}::same::execution-conditional:runIf:sha256:")
    assert "::identity-sha256:" in refs[0]
    assert refs[1:] == [
        f"{path}::same",
        f"{path}::alpha",
        f"{path}::alpha#2",
    ]


def test_frontend_inventory_rejects_titles_that_collide_with_occurrence_refs() -> None:
    with pytest.raises(guard.TestCorpusGuardError, match="test title is invalid"):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            'test("alpha#2", () => {});',
        )


def test_frontend_inventory_rejects_nested_destructuring_shadowing() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="nested destructuring",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            """
const { fixtures: { it } } = helpers;
it("shadowed", () => {});
""",
        )


def test_frontend_inventory_includes_supported_modifiers() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        """
const featureEnabled = true;
it.skipIf(process.platform === "win32")("skips on Windows", () => {});
test.runIf(featureEnabled)("runs when enabled", () => {});
it.sequential("runs in sequence", () => {});
test.fail("records an expected failure", () => {});
test.fixme("records an unavailable case", () => {});
test("declared test", async () => {
  test.fail(runtimeCondition, "runtime annotation");
  test.fixme(runtimeCondition, "runtime annotation");
});
""",
    )

    refs = [item.ref for item in declarations]
    assert refs[0].startswith(
        "apps/control-center/src/example.test.tsx::skips on Windows"
        "::execution-conditional:skipIf:sha256:"
    )
    assert "::identity-sha256:" in refs[0]
    assert refs[1].startswith(
        "apps/control-center/src/example.test.tsx::runs when enabled"
        "::execution-conditional:runIf:sha256:"
    )
    assert "::identity-sha256:" in refs[1]
    assert refs[2] == "apps/control-center/src/example.test.tsx::runs in sequence"
    assert refs[3].startswith(
        "apps/control-center/src/example.test.tsx::records an expected failure"
        "::execution-expected-failure:fail::identity-sha256:"
    )
    assert refs[4].startswith(
        "apps/control-center/src/example.test.tsx::records an unavailable case"
        "::execution-disabled:fixme::identity-sha256:"
    )
    assert refs[5] == "apps/control-center/src/example.test.tsx::declared test"


@pytest.mark.parametrize("modifier", ("skip", "fixme", "todo"))
def test_frontend_inventory_binds_execution_disabling_modifiers(
    modifier: str,
) -> None:
    active_ref = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        'test("case", () => {});',
    )[0].ref
    disabled_ref = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        f'test.{modifier}("case", () => {{}});',
    )[0].ref

    assert active_ref != disabled_ref
    assert f"::execution-disabled:{modifier}::identity-sha256:" in disabled_ref


@pytest.mark.parametrize("modifier", ("fail", "fails"))
def test_frontend_inventory_binds_expected_failure_modifiers(
    modifier: str,
) -> None:
    active_ref = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        'test("case", () => {});',
    )[0].ref
    expected_failure_ref = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        f'test.{modifier}("case", () => {{ throw new Error("expected"); }});',
    )[0].ref

    assert active_ref != expected_failure_ref
    assert (
        f"::execution-expected-failure:{modifier}::identity-sha256:"
        in expected_failure_ref
    )


@pytest.mark.parametrize("modifier", ("runIf", "skipIf"))
def test_frontend_inventory_binds_conditional_execution_modifiers(
    modifier: str,
) -> None:
    first_ref = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        f'const featureEnabled = true;\ntest.{modifier}(featureEnabled)("case", () => {{}});',
    )[0].ref
    second_ref = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        f'const featureEnabled = true;\ntest.{modifier}(!featureEnabled)("case", () => {{}});',
    )[0].ref

    assert first_ref != second_ref
    assert f"::execution-conditional:{modifier}:sha256:" in first_ref


def test_frontend_inventory_binds_conditional_local_initializer() -> None:
    path = "apps/control-center/src/example.test.tsx"
    source = 'const disabled = false;\ntest.skipIf(disabled)("case", () => {});'

    before = guard.parse_frontend_declarations(path, source)[0].ref
    after = guard.parse_frontend_declarations(
        path,
        source.replace("false", "true"),
    )[0].ref

    assert before != after


def test_frontend_inventory_binds_all_conditional_expression_identifiers() -> None:
    path = "apps/control-center/src/example.test.tsx"
    source = (
        'const disabled = false;\ntest.skipIf(disabled === true)("case", () => {});'
    )

    before = guard.parse_frontend_declarations(path, source)[0].ref
    after = guard.parse_frontend_declarations(
        path,
        source.replace("false", "true"),
    )[0].ref

    assert before != after


@pytest.mark.parametrize("literal", ("true", "false", "null", "undefined"))
def test_frontend_inventory_accepts_conditional_primitive_literals(
    literal: str,
) -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        f'test.skipIf({literal})("case", () => {{}});',
    )

    assert len(declarations) == 1


def test_frontend_inventory_binds_direct_and_suite_option_identifiers() -> None:
    path = "apps/control-center/src/example.test.tsx"

    def refs_for(disabled: bool, declaration: str) -> tuple[str, ...]:
        source = f"const disabled = {str(disabled).lower()};\n{declaration}"
        return tuple(
            item.ref for item in guard.parse_frontend_declarations(path, source)
        )

    direct = 'test("direct", { skip: disabled }, () => {});\n'
    suite = (
        'describe("suite", { skip: disabled }, () => {\n'
        '  test("nested", () => {});\n'
        "});\n"
    )
    assert refs_for(False, direct) != refs_for(True, direct)
    assert refs_for(False, suite) != refs_for(True, suite)


def test_frontend_inventory_binds_runtime_callback_skip_posture() -> None:
    path = "apps/control-center/src/example.test.tsx"
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="runtime callback skip",
    ):
        guard.parse_frontend_declarations(
            path,
            'test("case", context => { if (true) context.skip(); });',
        )

    assert guard.parse_frontend_declarations(
        path,
        'test("case", () => { test.skip(true, "runtime annotation"); });',
    )


@pytest.mark.parametrize(
    "callback",
    (
        "context => { const skip = context.skip; skip(); }",
        "context => { const { skip } = context; skip(); }",
        "context => { const { skip: stop } = context; stop(); }",
        "context => { const stop = context['skip']; const later = stop; later(); }",
        "function ({ skip: stop }) { stop(); }",
        "context => { const stop = context.skip; stop.call(context); }",
        "context => { const stop = context.skip; Reflect.apply(stop, context, []); }",
        "context => { let stop; stop = context.skip; stop(); }",
        "context => { const { ...rest } = context; rest.skip(); }",
        "context => { const stop = context[`skip`]; stop(); }",
        r'context => { const stop = context["sk\x69p"]; stop(); }',
        'context => { const stop = context["sk" + "ip"]; stop(); }',
        "({[`skip`]: stop}) => stop()",
        r'({["sk\x69p"]: stop}) => stop()',
        '({["sk" + "ip"]: stop}) => stop()',
        "context => { const copy = context; copy.skip(); }",
        "context => { const copy = context; const stop = copy.skip; stop(); }",
        "context => { let copy; copy = context; copy.skip(); }",
        "context => { ({skip: stop} = context); stop(); }",
        "context => { const {skip: stop} = (context); stop(); }",
        'context => Reflect.get(context, "skip")()',
        'context => { const stop = Object.getOwnPropertyDescriptor(context, "skip").value; stop(); }',
        "context => { const copy = {...context}; copy.skip(); }",
        "context => { const copy = Object.assign({}, context); copy.skip(); }",
    ),
)
def test_frontend_inventory_rejects_aliased_runtime_callback_skip(
    callback: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="runtime callback skip",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            f'test("case", {callback});',
        )


def test_frontend_inventory_allows_callback_context_alias_without_skip() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        'test("case", context => { const copy = context; void copy.task; });',
    )

    assert len(declarations) == 1


@pytest.mark.parametrize(
    "helper_source",
    (
        "function stop(context) { return context; }",
        "const stop = context => context;",
    ),
)
def test_frontend_inventory_binds_context_forwarding_helpers(
    helper_source: str,
) -> None:
    path = "apps/control-center/src/example.test.tsx"
    test_source = '\ntest("case", context => stop(context));'
    active = guard.parse_frontend_declarations(
        path,
        helper_source + test_source,
    )[0].ref
    skipped = guard.parse_frontend_declarations(
        path,
        helper_source.replace(
            "return context", "context.skip(); return context"
        ).replace(
            "context => context", "context => { context.skip(); return context; }"
        )
        + test_source,
    )[0].ref

    assert active != skipped


def test_frontend_inventory_binds_imported_context_forwarding_helper(
    tmp_path: Path,
) -> None:
    helper_path = tmp_path / "apps/control-center/src/helper.ts"
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text(
        "export function stop(context: { skip(): void }) { return context; }\n"
    )
    test_path = "apps/control-center/src/example.test.tsx"
    test_source = (
        'import { stop } from "./helper";\ntest("case", context => stop(context));'
    )
    active = guard._parse_worktree_test_declarations(
        tmp_path,
        test_path,
        test_source,
    )[0].ref
    helper_path.write_text(
        "export function stop(context: { skip(): void }) { "
        "context.skip(); return context; }\n"
    )
    skipped = guard._parse_worktree_test_declarations(
        tmp_path,
        test_path,
        test_source,
    )[0].ref

    assert active != skipped


def test_frontend_inventory_binds_transitive_context_forwarding_helpers() -> None:
    path = "apps/control-center/src/example.test.tsx"
    source = (
        "function inner(context) { return context; }\n"
        "function stop(context) { return inner(context); }\n"
        'test("case", context => stop(context));'
    )
    active = guard.parse_frontend_declarations(path, source)[0].ref
    skipped = guard.parse_frontend_declarations(
        path,
        source.replace(
            "function inner(context) { return context; }",
            "function inner(context) { context.skip(); return context; }",
        ),
    )[0].ref

    assert active != skipped


def test_frontend_inventory_binds_later_context_parameter_forwarding() -> None:
    path = "apps/control-center/src/example.test.tsx"
    source = (
        "function inner(context) { return context; }\n"
        "function stop(value, context) { return inner(context); }\n"
        'test("case", context => stop(1, context));'
    )
    active = guard.parse_frontend_declarations(path, source)[0].ref
    skipped = guard.parse_frontend_declarations(
        path,
        source.replace(
            "function inner(context) { return context; }",
            "function inner(context) { context.skip(); return context; }",
        ),
    )[0].ref

    assert active != skipped


def test_frontend_inventory_binds_aliased_and_captured_context_forwarding() -> None:
    path = "apps/control-center/src/example.test.tsx"
    for source in (
        "function inner(context) { return context; }\n"
        "function stop(context) { const copy = context; return inner(copy); }\n"
        'test("case", context => stop(context));',
        "let saved;\nfunction inner() { return saved; }\n"
        "function stop(context) { saved = context; return inner(); }\n"
        'test("case", context => stop(context));',
    ):
        active = guard.parse_frontend_declarations(path, source)[0].ref
        skipped = guard.parse_frontend_declarations(
            path,
            source.replace("return saved", "saved.skip(); return saved").replace(
                "return context; }\nfunction stop",
                "context.skip(); return context; }\nfunction stop",
            ),
        )[0].ref
        assert active != skipped


def test_frontend_inventory_binds_context_member_dispatch() -> None:
    path = "apps/control-center/src/example.test.tsx"
    source = (
        "const helpers = { inner: context => context };\n"
        "function stop(context) { return helpers.inner(context); }\n"
        'test("case", context => stop(context));'
    )
    changed = source.replace(
        "inner: context => context",
        "inner: context => { context.skip(); return context; }",
    )

    active = guard.parse_frontend_declarations(path, source)[0].ref
    try:
        skipped = guard.parse_frontend_declarations(path, changed)[0].ref
    except guard.TestCorpusGuardError:
        return
    assert active != skipped


def test_frontend_inventory_rejects_name_only_opaque_context_helper() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="binding cannot be resolved safely",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            "let helpers = {inner: context => context};\n"
            "function stop(context) { return helpers.inner(context); }\n"
            'test("case", context => stop(context));',
        )


@pytest.mark.parametrize(
    "source, changed",
    (
        (
            "function stop(context) { return opaque(context); }\n"
            'test("case", context => stop(context));',
            "function stop(context) { context.skip(); return opaque(context); }\n"
            'test("case", context => stop(context));',
        ),
        (
            "const saved = []; function inner() { return saved[0]; }\n"
            "function stop(context) { saved[0] = context; return inner(); }\n"
            'test("case", context => stop(context));',
            "const saved = []; function inner() { saved[0].skip(); return saved[0]; }\n"
            "function stop(context) { saved[0] = context; return inner(); }\n"
            'test("case", context => stop(context));',
        ),
        (
            "function inner(context) { return context; }\n"
            "function stop(context) { const run = inner; return run(context); }\n"
            'test("case", context => stop(context));',
            "function inner(context) { context.skip(); return context; }\n"
            "function stop(context) { const run = inner; return run(context); }\n"
            'test("case", context => stop(context));',
        ),
        (
            "const saved = []; function inner() { return saved[0]; }\n"
            "function stop(context) { saved.push(context); return inner(); }\n"
            'test("case", context => stop(context));',
            "const saved = []; function inner() { saved[0].skip(); return saved[0]; }\n"
            "function stop(context) { saved.push(context); return inner(); }\n"
            'test("case", context => stop(context));',
        ),
        (
            "let saved; function sink(value) { saved = value; }\n"
            "function inner() { return saved; }\n"
            "function stop(context) { sink(context); return inner(); }\n"
            'test("case", context => stop(context));',
            "let saved; function sink(value) { saved = value; }\n"
            "function inner() { saved.skip(); return saved; }\n"
            "function stop(context) { sink(context); return inner(); }\n"
            'test("case", context => stop(context));',
        ),
        (
            "function inner(value) { return value; }\n"
            "function stop(context) { return [context].map(inner); }\n"
            'test("case", context => stop(context));',
            "function inner(value) { value.skip(); return value; }\n"
            "function stop(context) { return [context].map(inner); }\n"
            'test("case", context => stop(context));',
        ),
        (
            "function inner(value) { return value; }\n"
            "function stop(context) { return [\ncontext\n].map(inner); }\n"
            'test("case", context => stop(context));',
            "function inner(value) { value.skip(); return value; }\n"
            "function stop(context) { return [\ncontext\n].map(inner); }\n"
            'test("case", context => stop(context));',
        ),
        (
            "function inner(value) { return value; }\n"
            "function stop(context) { return [context]?.map(inner); }\n"
            'test("case", context => stop(context));',
            "function inner(value) { value.skip(); return value; }\n"
            "function stop(context) { return [context]?.map(inner); }\n"
            'test("case", context => stop(context));',
        ),
        (
            "function inner(value) { return value; }\n"
            "function stop(context) { return Array.from([context], inner); }\n"
            'test("case", context => stop(context));',
            "function inner(value) { value.skip(); return value; }\n"
            "function stop(context) { return Array.from([context], inner); }\n"
            'test("case", context => stop(context));',
        ),
        (
            "function inner(value) { return value; }\n"
            "function stop(context) { return Reflect.apply(inner, null, [context]); }\n"
            'test("case", context => stop(context));',
            "function inner(value) { value.skip(); return value; }\n"
            "function stop(context) { return Reflect.apply(inner, null, [context]); }\n"
            'test("case", context => stop(context));',
        ),
        (
            "function inner(value) { return value; }\n"
            "function stop(context) { return Promise.resolve(context).then(inner); }\n"
            'test("case", context => stop(context));',
            "function inner(value) { value.skip(); return value; }\n"
            "function stop(context) { return Promise.resolve(context).then(inner); }\n"
            'test("case", context => stop(context));',
        ),
        (
            "function inner(value) { return value; }\n"
            "function stop(context) { const values = [context]; return values.map(inner); }\n"
            'test("case", context => stop(context));',
            "function inner(value) { value.skip(); return value; }\n"
            "function stop(context) { const values = [context]; return values.map(inner); }\n"
            'test("case", context => stop(context));',
        ),
        (
            "function inner(value) { return value; }\n"
            "function stop(context) { return new Set([context]).forEach(inner); }\n"
            'test("case", context => stop(context));',
            "function inner(value) { value.skip(); return value; }\n"
            "function stop(context) { return new Set([context]).forEach(inner); }\n"
            'test("case", context => stop(context));',
        ),
        (
            "function inner(value) { return value; }\n"
            "function get() { return inner; }\n"
            "function stop(context) { return Array.from([context], get()); }\n"
            'test("case", context => stop(context));',
            "function inner(value) { value.skip(); return value; }\n"
            "function get() { return inner; }\n"
            "function stop(context) { return Array.from([context], get()); }\n"
            'test("case", context => stop(context));',
        ),
        (
            "function inner(value) { return value; }\n"
            'function stop(context) { return [context]["map"](inner); }\n'
            'test("case", context => stop(context));',
            "function inner(value) { value.skip(); return value; }\n"
            'function stop(context) { return [context]["map"](inner); }\n'
            'test("case", context => stop(context));',
        ),
    ),
)
def test_frontend_inventory_closes_escaped_context_flow(
    source: str,
    changed: str,
) -> None:
    path = "apps/control-center/src/example.test.tsx"

    try:
        active = guard.parse_frontend_declarations(path, source)[0].ref
        skipped = guard.parse_frontend_declarations(path, changed)[0].ref
    except guard.TestCorpusGuardError:
        return
    assert active != skipped


def test_frontend_inventory_binds_test_for_context_helper() -> None:
    path = "apps/control-center/src/example.test.tsx"
    source = (
        "function stop(context) { return context; }\n"
        'test.for([[1]])("case", (_row, context) => stop(context));'
    )
    changed = source.replace(
        "return context",
        "context.skip(); return context",
    )

    assert guard.parse_frontend_declarations(path, source)[0].ref != (
        guard.parse_frontend_declarations(path, changed)[0].ref
    )

    typed_source = source.replace(
        "(_row, context)",
        "(_row: number[], context: TestContext)",
    )
    typed_changed = typed_source.replace(
        "return context",
        "context.skip(); return context",
    )
    assert guard.parse_frontend_declarations(path, typed_source)[0].ref != (
        guard.parse_frontend_declarations(path, typed_changed)[0].ref
    )


@pytest.mark.parametrize(
    "callback",
    (
        "(_row, context) => context.skip()",
        "(_row, {skip}) => skip()",
    ),
)
def test_frontend_inventory_rejects_test_for_runtime_skip(callback: str) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="runtime callback skip",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            f'test.for([[1]])("case", {callback});',
        )


def test_frontend_inventory_does_not_treat_each_row_as_context() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        'test.each([[{skip: "value"}]])("case", ({skip}) => expect(skip).toBe("value"));',
    )

    assert len(declarations) == 1


def test_frontend_inventory_classifies_named_parameterized_callbacks() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="runtime callback skip",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            "const handler = (_row: number[], {skip}: TestContext) => skip();\n"
            'test.for([[1]])("case", handler);',
        )

    assert guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        "const handler = row => row.skip();\n"
        'test.each([[{skip() { return "row"; }}]])("case", handler);',
    )


def test_frontend_inventory_ignores_shadowed_dormant_context_helper() -> None:
    path = "apps/control-center/src/example.test.tsx"
    source = (
        "function inner(context) { return context; }\n"
        "function stop(context) { "
        "function dormant(context) { return inner(context); } return context; }\n"
        'test("case", context => stop(context));'
    )
    changed = source.replace(
        "return inner(context)",
        "return String(inner(context))",
    )

    assert guard.parse_frontend_declarations(path, source)[0].ref == (
        guard.parse_frontend_declarations(path, changed)[0].ref
    )


def test_frontend_inventory_binds_imported_transitive_context_helper(
    tmp_path: Path,
) -> None:
    helper_path = tmp_path / "apps/control-center/src/helper.ts"
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text(
        "function inner(context: { skip(): void }) { return context; }\n"
        "export function stop(context: { skip(): void }) { return inner(context); }\n"
    )
    test_path = "apps/control-center/src/example.test.tsx"
    test_source = (
        'import { stop } from "./helper";\ntest("case", context => stop(context));'
    )
    active = guard._parse_worktree_test_declarations(
        tmp_path,
        test_path,
        test_source,
    )[0].ref
    helper_path.write_text(
        "function inner(context: { skip(): void }) { "
        "context.skip(); return context; }\n"
        "export function stop(context: { skip(): void }) { return inner(context); }\n"
    )
    skipped = guard._parse_worktree_test_declarations(
        tmp_path,
        test_path,
        test_source,
    )[0].ref

    assert active != skipped


@pytest.mark.parametrize(
    "active_helper, changed_helper",
    (
        (
            "function inner(context: { skip(): void }) { return context; }\n"
            "export function stop(context: { skip(): void }) { "
            "const values = [context]; return values.map(inner); }\n",
            "function inner(context: { skip(): void }) { "
            "context.skip(); return context; }\n"
            "export function stop(context: { skip(): void }) { "
            "const values = [context]; return values.map(inner); }\n",
        ),
        (
            "function inner(context: { skip(): void }) { return context; }\n"
            "function get() { return inner; }\n"
            "export function stop(context: { skip(): void }) { "
            "return Array.from([context], get()); }\n",
            "function inner(context: { skip(): void }) { "
            "context.skip(); return context; }\n"
            "function get() { return inner; }\n"
            "export function stop(context: { skip(): void }) { "
            "return Array.from([context], get()); }\n",
        ),
        (
            "function inner(context: { skip(): void }) { return context; }\n"
            "export function stop(context: { skip(): void }) { "
            'return [context]["map"](inner); }\n',
            "function inner(context: { skip(): void }) { "
            "context.skip(); return context; }\n"
            "export function stop(context: { skip(): void }) { "
            'return [context]["map"](inner); }\n',
        ),
    ),
)
def test_frontend_inventory_closes_imported_derived_context_flow(
    tmp_path: Path,
    active_helper: str,
    changed_helper: str,
) -> None:
    helper_path = tmp_path / "apps/control-center/src/helper.ts"
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text(active_helper)
    test_path = "apps/control-center/src/example.test.tsx"
    test_source = (
        'import { stop } from "./helper";\ntest("case", context => stop(context));'
    )
    try:
        active = guard._parse_worktree_test_declarations(
            tmp_path,
            test_path,
            test_source,
        )[0].ref
        helper_path.write_text(changed_helper)
        changed = guard._parse_worktree_test_declarations(
            tmp_path,
            test_path,
            test_source,
        )[0].ref
    except guard.TestCorpusGuardError:
        return
    assert active != changed


def test_frontend_inventory_rejects_circular_context_helper_closure() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="circular",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            "function inner(context) { return stop(context); }\n"
            "function stop(context) { return inner(context); }\n"
            'test("case", context => stop(context));',
        )


@pytest.mark.parametrize(
    "callback",
    (
        "handler",
        "(...args) => args[0].skip()",
        "function () { arguments[0].skip(); }",
        "({ skip = () => {} }) => skip()",
    ),
)
def test_frontend_inventory_rejects_opaque_runtime_callback_skip(
    callback: str,
) -> None:
    source = (
        "const handler = context => context.skip();\n" if callback == "handler" else ""
    )
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="runtime callback skip",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            source + f'test("case", {callback});',
        )


@pytest.mark.parametrize(
    "source",
    (
        'test.for([[1]])("case", (...args) => args[1].skip());',
        'test.for([[1]])("case", function () { arguments[1].skip(); });',
        'test("case", (...args) => { const context = args[0]; context.skip(); });',
        'test("case", (...args) => { const [context] = args; context.skip(); });',
        'test.for([[1]])("case", function () { '
        "const context = arguments[1]; context.skip(); });",
        'test.for([[1]])("case", function () { '
        "const [, context] = arguments; context.skip(); });",
        'test.for([[1]])("case", (...args) => Reflect.get(args[1], "skip")());',
        "const handler: TestCallback = (...args) => args[0].skip();\n"
        'test("case", handler);',
        "const handler: (context: TestContext) => void = "
        "context => context.skip();\n"
        'test("case", handler);',
        "const handler = ((...args) => args[0].skip()) as TestCallback;\n"
        'test("case", handler);',
        "const handler = ((...args) => args[0].skip()) satisfies TestCallback;\n"
        'test("case", handler);',
        "const first = (...args) => args[0].skip();\n"
        "const handler = first;\n"
        'test("case", handler);',
    ),
)
def test_frontend_inventory_rejects_indirect_runtime_callback_skip(
    source: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="runtime callback skip",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            source,
        )


@pytest.mark.parametrize(
    "callback",
    (
        "(...args) => args[0].skip()",
        "function () { arguments[0].skip(); }",
        "(...args) => { const [row] = args; row.skip(); }",
        "function () { const [row] = arguments; row.skip(); }",
    ),
)
def test_frontend_inventory_keeps_each_row_callback_active(callback: str) -> None:
    assert (
        len(
            guard.parse_frontend_declarations(
                "apps/control-center/src/example.test.tsx",
                f'test.each([[{{skip() {{ return "row"; }}}}]])("case", {callback});',
            )
        )
        == 1
    )


def test_frontend_inventory_binds_conditional_imported_initializer(
    tmp_path: Path,
) -> None:
    test_path = "apps/control-center/src/example.test.ts"
    source_path = tmp_path / "apps/control-center/src/flags.ts"
    source_path.parent.mkdir(parents=True)
    source_path.write_text("export const disabled = false;\n")
    test_text = (
        'import { disabled } from "./flags";\n'
        'test.skipIf(disabled)("case", () => {});\n'
    )

    before = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)
    source_path.write_text("export const disabled = true;\n")
    after = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)

    assert before[0].ref != after[0].ref


def test_frontend_inventory_binds_named_import_initialization_closure(
    tmp_path: Path,
) -> None:
    test_path = "apps/control-center/src/example.test.ts"
    helper_path = tmp_path / "apps/control-center/src/helper.ts"
    state_path = tmp_path / "apps/control-center/src/state.ts"
    helper_path.parent.mkdir(parents=True)
    state_path.write_text("export const state = 'one';\n")
    helper_path.write_text(
        'import { state } from "./state";\nexport const UNUSED = state;\n'
    )
    test_text = 'import { UNUSED } from "./helper";\ntest("case", () => {});\n'

    before = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)
    helper_path.write_text(
        'import { beforeEach } from "vitest";\n'
        'import "./state";\n'
        "beforeEach(context => context.skip());\n"
        "export const UNUSED = 'bound';\n"
    )
    collection_changed = guard._parse_worktree_test_declarations(
        tmp_path,
        test_path,
        test_text,
    )
    state_path.write_text("export const state = 'two';\n")
    transitive_changed = guard._parse_worktree_test_declarations(
        tmp_path,
        test_path,
        test_text,
    )

    assert before[0].ref != collection_changed[0].ref
    assert collection_changed[0].ref != transitive_changed[0].ref


def test_frontend_inventory_ignores_inert_named_import_changes(tmp_path: Path) -> None:
    test_path = "apps/control-center/src/example.test.ts"
    helper_path = tmp_path / "apps/control-center/src/helper.ts"
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text(
        "export const UNUSED = 'one';\n"
        "export function test(value: string) { return value; }\n"
        "export const Copy = () => <p>it works</p>;\n"
    )
    test_text = 'import { UNUSED } from "./helper";\ntest("case", () => {});\n'

    before = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)
    helper_path.write_text(
        "export const UNUSED = 'two';\n"
        "export function test(value: string) { return value; }\n"
        "export const Copy = () => <p>it still works</p>;\n"
    )
    after = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)

    assert before == after


@pytest.mark.parametrize(
    "posture_source",
    (
        "const hook = beforeEach; hook(context => context.skip());",
        "let hook; hook = beforeEach; hook(context => context.skip());",
        "const hook = (beforeEach); hook(context => context.skip());",
        "const {beforeEach: hook} = globalThis; hook(context => context.skip());",
        "globalThis.beforeEach(context => context.skip());",
        "globalThis['beforeEach'](context => context.skip());",
        "globalThis[`beforeEach`](context => context.skip());",
        r'globalThis["before\x45ach"](context => context.skip());',
        'globalThis["before" + "Each"](context => context.skip());',
    ),
)
def test_frontend_inventory_binds_indirect_imported_runtime_posture(
    tmp_path: Path,
    posture_source: str,
) -> None:
    test_path = "apps/control-center/src/example.test.ts"
    helper_path = tmp_path / "apps/control-center/src/helper.ts"
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text("export const UNUSED = 'one';\n")
    test_text = 'import { UNUSED } from "./helper";\ntest("case", () => {});\n'

    before = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)
    helper_path.write_text(f"{posture_source}\nexport const UNUSED = 'one';\n")
    after = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)

    assert before[0].ref != after[0].ref


@pytest.mark.parametrize(
    "registration",
    (
        'test.skip("case", () => {})',
        'test.only("case", () => {})',
        'test.each([[1]])("case", () => {})',
        'describe.skip("suite", () => {})',
        'suite.only("suite", () => {})',
        'it.todo("case")',
        'test?.("case", () => {})',
        '(test)("case", () => {})',
    ),
)
def test_frontend_inventory_binds_imported_global_registration_initializer(
    tmp_path: Path,
    registration: str,
) -> None:
    test_path = "apps/control-center/src/example.test.ts"
    helper_path = tmp_path / "apps/control-center/src/helper.ts"
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text(f"export const marker = true;\n{registration};\n")
    test_text = (
        'import { marker } from "./helper";\ntest("outer", () => { void marker; });\n'
    )

    before = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)
    helper_path.write_text(
        f"export const marker = true;\nconst changed = true;\n{registration};\n"
    )
    after = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)

    assert before[0].ref != after[0].ref


@pytest.mark.parametrize(
    "inert_source",
    (
        "export const copy = 'import(\"vitest\")';\n",
        '// import("vitest")\nexport const copy = true;\n',
        '/* require("@playwright/test") */\nexport const copy = true;\n',
        "export const copy = `test.skip('not code')`;\n",
    ),
)
def test_frontend_inventory_ignores_inert_runner_syntax_in_imported_initializer(
    tmp_path: Path,
    inert_source: str,
) -> None:
    test_path = "apps/control-center/src/example.test.ts"
    helper_path = tmp_path / "apps/control-center/src/helper.ts"
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text(inert_source)
    test_text = (
        'import { copy } from "./helper";\ntest("outer", () => { void copy; });\n'
    )

    before = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)
    helper_path.write_text(inert_source + "export const changed = true;\n")
    after = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)

    assert before[0].ref == after[0].ref


@pytest.mark.parametrize(
    "interpolation",
    (
        "beforeEach(() => {})",
        "test.skip('case', () => {})",
    ),
)
def test_frontend_inventory_binds_runner_syntax_in_template_interpolation(
    tmp_path: Path,
    interpolation: str,
) -> None:
    test_path = "apps/control-center/src/example.test.ts"
    helper_path = tmp_path / "apps/control-center/src/helper.ts"
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text(f"export const value = `${{{interpolation}}}`;\n")
    test_text = (
        'import { value } from "./helper";\ntest("outer", () => { void value; });\n'
    )

    before = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)
    helper_path.write_text(
        f"const changed = true;\nexport const value = `${{{interpolation}}}`;\n"
    )
    after = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)

    assert before[0].ref != after[0].ref


@pytest.mark.parametrize(
    "loader",
    (
        'const child = require("./child"); void child;',
        'void import("./child");',
        'export * as child from "./child";',
    ),
)
def test_frontend_inventory_binds_runtime_loader_dependency(
    tmp_path: Path,
    loader: str,
) -> None:
    test_path = "apps/control-center/src/example.test.ts"
    helper_path = tmp_path / "apps/control-center/src/helper.ts"
    child_path = tmp_path / "apps/control-center/src/child.ts"
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text(f"{loader}\nexport const marker = true;\n")
    child_path.write_text("beforeEach(() => {});\n")
    test_text = (
        'import { marker } from "./helper";\ntest("outer", () => { void marker; });\n'
    )

    before = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)
    child_path.write_text("const changed = true;\nbeforeEach(() => {});\n")
    after = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)

    assert before[0].ref != after[0].ref


@pytest.mark.parametrize(
    "loader",
    (
        'const v = require?.("vitest"); v.beforeEach(() => {});',
        'const v = (require)("vitest"); v.beforeEach(() => {});',
        "const v = require(`vitest`); v.beforeEach(() => {});",
        "void import(`vitest`);",
        'const {test: check} = require?.("vitest"); check("case", () => {});',
    ),
)
def test_frontend_inventory_binds_supported_runner_loader_initializer(
    tmp_path: Path,
    loader: str,
) -> None:
    test_path = "apps/control-center/src/example.test.ts"
    helper_path = tmp_path / "apps/control-center/src/helper.ts"
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text(f"export const marker = true;\n{loader}\n")
    test_text = (
        'import { marker } from "./helper";\ntest("outer", () => { void marker; });\n'
    )

    before = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)
    helper_path.write_text(
        f"export const marker = true;\nconst changed = true;\n{loader}\n"
    )
    after = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)

    assert before[0].ref != after[0].ref


@pytest.mark.parametrize(
    "type_edge",
    (
        'export { type Foo } from "./child";',
        'import { /* comment */ type Foo } from "./child";',
        'import { type Foo, /* comment */ type Bar } from "./child";',
        'export type Page = import("@playwright/test").Page;',
        'export function page(): import("./child").Page { throw new Error(); }',
    ),
)
def test_frontend_inventory_ignores_type_only_initializer_edges(
    tmp_path: Path,
    type_edge: str,
) -> None:
    test_path = "apps/control-center/src/example.test.ts"
    helper_path = tmp_path / "apps/control-center/src/helper.ts"
    child_path = tmp_path / "apps/control-center/src/child.ts"
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text(f"{type_edge}\nexport const marker = true;\n")
    child_path.write_text("beforeEach(() => {});\n")
    test_text = (
        'import { marker } from "./helper";\ntest("outer", () => { void marker; });\n'
    )

    before = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)
    child_path.write_text("const changed = true;\nbeforeEach(() => {});\n")
    after = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)

    assert before == after


@pytest.mark.parametrize(
    "runtime_edge",
    (
        'const value = { child: import("./child") };',
        'const value = enabled ? import("./child") : Promise.resolve();',
        'import { type } from "./child"; void type;',
        'export { type as runtimeType } from "./child";',
    ),
)
def test_frontend_inventory_binds_runtime_edges_named_or_shaped_like_types(
    tmp_path: Path,
    runtime_edge: str,
) -> None:
    test_path = "apps/control-center/src/example.test.ts"
    helper_path = tmp_path / "apps/control-center/src/helper.ts"
    child_path = tmp_path / "apps/control-center/src/child.ts"
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text(
        f"const enabled = true;\n{runtime_edge}\nexport const marker = true;\n"
    )
    child_path.write_text("beforeEach(() => {});\nexport const type = true;\n")
    test_text = (
        'import { marker } from "./helper";\ntest("outer", () => { void marker; });\n'
    )

    before = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)
    child_path.write_text(
        "const changed = true;\nbeforeEach(() => {});\nexport const type = true;\n"
    )
    after = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)

    assert before[0].ref != after[0].ref


def test_frontend_inventory_ignores_uncalled_function_body_initializer() -> None:
    inert = (
        "export function dormant() { beforeEach(() => {}); return 1; }\n"
        "export const marker = true;\n"
    )
    changed = inert.replace("return 1", "return 2")

    assert frontend.frontend_runtime_test_posture(inert) is False
    assert frontend.frontend_runtime_identity_source(inert) == (
        frontend.frontend_runtime_identity_source(changed)
    )


def test_frontend_inventory_binds_called_function_body_initializer() -> None:
    active = (
        "function activate() { beforeEach(() => {}); return 1; }\n"
        "activate();\nexport const marker = true;\n"
    )
    changed = active.replace("return 1", "return 2")

    assert frontend.frontend_runtime_test_posture(active) is True
    assert frontend.frontend_runtime_identity_source(active) != (
        frontend.frontend_runtime_identity_source(changed)
    )


def test_frontend_inventory_binds_called_function_setup_skip_posture() -> None:
    active = (
        "function setup() { beforeEach(ctx => {}) }\n"
        'setup();\ntest("case", () => {});\n'
    )
    skipped = active.replace("ctx => {}", "ctx => ctx.skip()")

    active_ref = frontend.parse_frontend_refs(
        "apps/control-center/src/example.test.ts",
        active,
    )[0]
    skipped_ref = frontend.parse_frontend_refs(
        "apps/control-center/src/example.test.ts",
        skipped,
    )[0]

    assert active_ref != skipped_ref


@pytest.mark.parametrize(
    "inert",
    (
        "export const dormant = () => { beforeEach(() => {}); return 1; };",
        "export class Dormant { method() { beforeEach(() => {}); return 1; } }",
    ),
)
def test_frontend_inventory_ignores_uncalled_arrow_and_class_bodies(
    inert: str,
) -> None:
    changed = inert.replace("return 1", "return 2")

    assert frontend.frontend_runtime_test_posture(inert) is False
    assert frontend.frontend_runtime_identity_source(inert) == (
        frontend.frontend_runtime_identity_source(changed)
    )


def test_frontend_inventory_binds_called_arrow_body_initializer() -> None:
    active = (
        "const activate = async (): Promise<void> => { beforeEach(() => {}); "
        "await import('./child'); };\nactivate();"
    )

    assert frontend.frontend_runtime_test_posture(active) is True
    assert frontend.frontend_runtime_import_modules(active) == ("./child",)


@pytest.mark.parametrize(
    "active",
    (
        "class Setup { static apply() { beforeEach(() => {}); return 1; } }\n"
        "const install = Setup.apply; install();",
        "class Setup { apply() { beforeEach(() => {}); return 1; } }\n"
        "const setup = new Setup(); const install = setup.apply; install();",
        "class Setup { static apply() { beforeEach(() => {}); return 1; } }\n"
        'const install = Reflect.get(Setup, "apply"); install();',
        "class Setup { apply() { beforeEach(() => {}); return 1; } }\n"
        'const setup = new Setup(); Reflect.get(setup, "apply")();',
        "class Setup { apply() { beforeEach(() => {}); return 1; } }\n"
        "const setup = new Setup(); const copy = setup; copy.apply();",
        "class Setup { apply() { beforeEach(() => {}); return 1; } }\n"
        "const setup = new Setup(); const {apply: install} = setup; install();",
        "class Setup { apply() { beforeEach(() => {}); return 1; } }\n"
        'const setup = new Setup(); const key = "apply"; Reflect.get(setup, key)();',
        "class Setup { static apply() { beforeEach(() => {}); return 1; } }\n"
        'const Factory = Setup; Reflect.get(Factory, "apply")();',
        "class Setup { static apply() { beforeEach(() => {}); return 1; } }\n"
        "const Factory = (Setup); Factory.apply();",
        "class Setup { static apply() { beforeEach(() => {}); return 1; } }\n"
        "const items = [Setup]; items[0].apply();",
        "class Setup { static apply() { beforeEach(() => {}); return 1; } }\n"
        "registry.add(Setup); registry.run();",
        "const Factory = class Setup {\n"
        "static apply() { beforeEach(() => {}); return 1; } }; Factory.apply();",
        "const Factory = class Setup {\n"
        "static apply = () => { beforeEach(() => {}); return 1; } }; Factory.apply();",
        "const Factory: {apply(): number} = class Setup {\n"
        "static apply() { beforeEach(() => {}); return 1; } }; Factory.apply();",
        "const Factory = (class Setup {\n"
        "static apply() { beforeEach(() => {}); return 1; } }); Factory.apply();",
        "let Factory; Factory = class Setup {\n"
        "static apply() { beforeEach(() => {}); return 1; } }; Factory.apply();",
        "registry.Factory = class Setup {\n"
        "static apply() { beforeEach(() => {}); return 1; } }; registry.Factory.apply();",
        "(class Setup {\n"
        "static apply() { beforeEach(() => {}); return 1; } }).apply();",
        "(Factory = class Setup {\n"
        "static apply() { beforeEach(() => {}); return 1; } }).apply();",
        'registry["Factory"] = class Setup {\n'
        "static apply() { beforeEach(() => {}); return 1; } }; "
        'registry["Factory"].apply();',
        "const registry = { Factory: class Setup {\n"
        "static apply() { beforeEach(() => {}); return 1; } } }; "
        "registry.Factory.apply();",
        "const factories = [class Setup {\n"
        "static apply() { beforeEach(() => {}); return 1; } }]; "
        "factories[0].apply();",
        "const factories = new Map([['factory', class Setup {\n"
        "static apply() { beforeEach(() => {}); return 1; } }]]); "
        "factories.get('factory').apply();",
        "const Factory = enabled ? class Setup {\n"
        "static apply() { beforeEach(() => {}); return 1; } : fallback; "
        "Factory.apply();",
        "const Factory = class Setup {\n"
        "constructor() { beforeEach(() => {}); return 1; } }; new Factory();",
        "const Factory = class Setup {\n"
        "apply() { beforeEach(() => {}); return 1; } }; new Factory().apply();",
        "(class Setup {\n"
        'static apply() { beforeEach(() => {}); return 1; } })["apply"]();',
        "class Setup { apply() { beforeEach(() => {}); return 1; } }\n"
        'const setup = new Setup(); const key = "apply"; setup[key]();',
        "class Setup { apply() { beforeEach(() => {}); return 1; } }\n"
        "const setup = new Setup(); let copy; copy = setup; copy.apply();",
        "class Setup { apply() { beforeEach(() => {}); return 1; } }\n"
        "const setup = new Setup(); let install; ({apply: install} = setup); install();",
        "class Setup { apply() { beforeEach(() => {}); return 1; } }\n"
        'const setup = new Setup(); Object.getOwnPropertyDescriptor(setup, "apply").value();',
        "class Setup { apply() { beforeEach(() => {}); return 1; } }\n"
        "const setup = new Setup(); invoke(setup); function invoke(target) { target.apply(); }",
        "class Setup { apply() { beforeEach(() => {}); return 1; } }\n"
        'Reflect.get(Setup.prototype, "apply")();',
        "class Setup { apply() { beforeEach(() => {}); return 1; } }\n"
        'Object.getOwnPropertyDescriptor(Setup.prototype, "apply").value.call(new Setup());',
    ),
)
def test_frontend_inventory_binds_reflectively_called_class_method_initializer(
    active: str,
) -> None:
    changed = active.replace("return 1", "return 2")

    assert frontend.frontend_runtime_test_posture(active) is True
    assert frontend.frontend_runtime_identity_source(active) != (
        frontend.frontend_runtime_identity_source(changed)
    )


def test_frontend_inventory_ignores_unused_named_class_expression() -> None:
    dormant = "const Factory = class Setup { static apply() { return 1; } };"
    changed = dormant.replace("return 1", "return 2")

    assert frontend.frontend_runtime_test_posture(dormant) is False
    assert frontend.frontend_runtime_identity_source(dormant) == (
        frontend.frontend_runtime_identity_source(changed)
    )


@pytest.mark.parametrize(
    "dormant",
    (
        'registry["Factory"] = class Setup { static apply() { return 1; } };',
        "const registry = { Factory: class Setup { static apply() { return 1; } } };",
        "const factories = [class Setup { static apply() { return 1; } }];",
    ),
)
def test_frontend_inventory_ignores_dormant_contained_class_expression(
    dormant: str,
) -> None:
    changed = dormant.replace("return 1", "return 2")

    assert frontend.frontend_runtime_test_posture(dormant) is False
    assert frontend.frontend_runtime_identity_source(dormant) == (
        frontend.frontend_runtime_identity_source(changed)
    )


def test_frontend_inventory_binds_imported_reflective_class_initializer(
    tmp_path: Path,
) -> None:
    helper_path = tmp_path / "apps/control-center/src/helper.ts"
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text(
        "class Setup { apply() { return 1; } }\n"
        "const setup = new Setup();\n"
        'const install = Reflect.get(setup, "apply"); install();\n'
        "export const marker = true;\n"
    )
    test_path = "apps/control-center/src/example.test.tsx"
    test_source = (
        'import { marker } from "./helper";\ntest("case", () => { void marker; });'
    )
    active = guard._parse_worktree_test_declarations(
        tmp_path,
        test_path,
        test_source,
    )[0].ref
    helper_path.write_text(
        "class Setup { apply() { beforeEach(() => {}); return 1; } }\n"
        "const setup = new Setup();\n"
        'const install = Reflect.get(setup, "apply"); install();\n'
        "export const marker = true;\n"
    )
    changed = guard._parse_worktree_test_declarations(
        tmp_path,
        test_path,
        test_source,
    )[0].ref

    assert active != changed


def test_frontend_inventory_ignores_reflection_in_dormant_function() -> None:
    inert = (
        "class Setup { apply() { beforeEach(() => {}); return 1; } }\n"
        'function dormant() { Reflect.get(new Setup(), "apply")(); }'
    )
    changed = inert.replace("return 1", "return 2")

    assert frontend.frontend_runtime_test_posture(inert) is False
    assert frontend.frontend_runtime_identity_source(inert) == (
        frontend.frontend_runtime_identity_source(changed)
    )


@pytest.mark.parametrize(
    "active",
    (
        "class Setup { apply() { beforeEach(() => {}); return 1; } }\n"
        "function build() { return new Setup(); } build().apply();",
        "class Setup { apply() { beforeEach(() => {}); return 1; } }\n"
        "const setup = new Setup(); const items = [setup]; items[0].apply();",
        "class Setup { apply() { beforeEach(() => {}); return 1; } }\n"
        "const setup = new Setup(); registry.invoke(setup);",
    ),
)
def test_frontend_inventory_binds_derived_class_receivers(active: str) -> None:
    changed = active.replace("return 1", "return 2")

    assert frontend.frontend_runtime_test_posture(active) is True
    assert frontend.frontend_runtime_identity_source(active) != (
        frontend.frontend_runtime_identity_source(changed)
    )


@pytest.mark.parametrize(
    "mask_builder",
    (
        frontend._runtime_import_code_mask,
        frontend._module_initializer_code_mask,
    ),
)
def test_frontend_lexical_mask_cache_returns_isolated_mutable_views(
    mask_builder: Callable[[str], bytearray],
) -> None:
    source = "function dormant() { return import('./child'); }\n"

    first = mask_builder(source)
    second = mask_builder(source)
    expected = bytearray(second)

    assert first == second
    assert first is not second
    first[:] = b"\x00" * len(first)
    assert mask_builder(source) == expected


def test_frontend_initializer_mask_cache_is_keyed_by_exact_source() -> None:
    cached_builder = frontend._module_initializer_code_mask_bytes
    cached_builder.cache_clear()
    first_source = "function dormant() { return 1; }\n"
    second_source = "function dormant() { return 2; }\n"

    try:
        cached_builder(first_source)
        after_first = cached_builder.cache_info()
        cached_builder(first_source)
        after_repeat = cached_builder.cache_info()
        cached_builder(second_source)
        after_change = cached_builder.cache_info()

        assert after_first.misses == 1
        assert after_repeat.hits == 1
        assert after_repeat.misses == 1
        assert after_change.hits == 1
        assert after_change.misses == 2
    finally:
        cached_builder.cache_clear()


def test_frontend_balanced_range_cache_is_keyed_by_exact_source() -> None:
    cached_skip = frontend._skip_balanced
    cached_skip.cache_clear()
    first_source = "(call())"
    second_source = "(call(()))"

    try:
        assert cached_skip(first_source, 0) == len(first_source)
        after_first = cached_skip.cache_info()
        assert cached_skip(first_source, 0) == len(first_source)
        after_repeat = cached_skip.cache_info()
        assert cached_skip(second_source, 0) == len(second_source)
        after_change = cached_skip.cache_info()

        assert after_first.misses == 1
        assert after_repeat.hits == 1
        assert after_repeat.misses == 1
        assert after_change.hits == 1
        assert after_change.misses == 2
    finally:
        cached_skip.cache_clear()


def test_frontend_inventory_preserves_conditional_literal_values() -> None:
    path = "apps/control-center/src/example.test.tsx"
    never_ref = guard.parse_frontend_declarations(
        path,
        'test.skipIf(process.env.MODE === "never")("case", () => {});',
    )[0].ref
    ci_ref = guard.parse_frontend_declarations(
        path,
        'test.skipIf(process.env.MODE === "ci")("case", () => {});',
    )[0].ref
    trivia_ref = guard.parse_frontend_declarations(
        path,
        'test.skipIf( process.env.MODE /* mode */ === "never" )("case", () => {});',
    )[0].ref

    assert never_ref != ci_ref
    assert never_ref == trivia_ref


def test_frontend_inventory_preserves_conditional_operator_boundaries() -> None:
    path = "apps/control-center/src/example.test.tsx"
    postfix_ref = guard.parse_frontend_declarations(
        path,
        "const state = {a: 1, b: 2};\n"
        'test.skipIf(state.a++ + state.b)("case", () => {});',
    )[0].ref
    prefix_ref = guard.parse_frontend_declarations(
        path,
        "const state = {a: 1, b: 2};\n"
        'test.skipIf(state.a + ++state.b)("case", () => {});',
    )[0].ref

    assert postfix_ref != prefix_ref


def test_frontend_inventory_structurally_binds_titles_and_execution() -> None:
    path = "apps/control-center/src/example.test.tsx"
    active_ref = guard.parse_frontend_declarations(
        path,
        'test("case::execution-disabled:skip", () => {});',
    )[0].ref
    disabled_ref = guard.parse_frontend_declarations(
        path,
        'test.skip("case", () => {});',
    )[0].ref

    assert active_ref != disabled_ref
    assert "::identity-sha256:" in active_ref
    assert "::identity-sha256:" in disabled_ref


def test_frontend_inventory_masks_nested_template_interpolations() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        """
const label = `prefix ${fn(`inner ${value("nested")}`)} suffix`;
const decoy = `test("not a declaration", () => {})`;
it("real test", () => {});
""",
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.test.tsx::real test",
    ]


def test_frontend_inventory_scans_executable_template_interpolations() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        'const registered = `${test("registered", () => {})}`;\n',
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.test.tsx::registered"
    ]


def test_frontend_inventory_rejects_runner_namespace_calls() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="namespace test API cannot be inventoried safely",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            """
import * as vitest from "vitest";
vitest.test("registered", () => {});
""",
        )


def test_frontend_inventory_rejects_dynamic_skipped_title() -> None:
    with pytest.raises(guard.TestCorpusGuardError, match="test title is invalid"):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            "test.skip(title, () => {});",
        )


def test_frontend_inventory_rejects_parameterized_suites() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="parameterized suites cannot be inventoried safely",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            """
describe.each([["one"], ["two"]])("suite %s", () => {
  test("nested", () => {});
});
""",
        )


def test_frontend_inventory_handles_comments_and_regex_literals() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.spec.ts",
        r"""
const patterns = [/path\//]; it /* lexical trivia */ ("after comment", () => {});
it.each([/path\//])("matches escaped slash", () => {});
""",
    )

    assert (
        declarations[0].ref == "apps/control-center/src/example.spec.ts::after comment"
    )
    assert declarations[1].ref.startswith(
        "apps/control-center/src/example.spec.ts::matches escaped slash::parameters-sha256:"
    )


def test_frontend_inventory_handles_regex_after_division_operator() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.spec.ts",
        r"""
const matched = value / /path\//.test(input);
const ratio = /path/ / divisor;
test("covered after division", () => matched);
""",
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.spec.ts::covered after division",
    ]


@pytest.mark.parametrize(
    "path",
    [
        "apps/control-center/src/example.test.js",
        "apps/control-center/src/example.spec.jsx",
        "apps/control-center/src/example.test.ts",
        "apps/control-center/src/example.spec.tsx",
        "apps/control-center/src/example.test.cjs",
        "apps/control-center/src/example.spec.cjsx",
        "apps/control-center/src/example.test.mjs",
        "apps/control-center/src/example.spec.mjsx",
        "apps/control-center/src/example.test.cts",
        "apps/control-center/src/example.spec.ctsx",
        "apps/control-center/src/example.test.mts",
        "apps/control-center/src/example.spec.mtsx",
    ],
)
def test_vitest_default_extensions_are_guarded(path: str) -> None:
    assert guard._is_test_path(path)


def test_discovery_covers_every_vitest_default_extension(tmp_path: Path) -> None:
    source_root = tmp_path / "apps/control-center/src"
    source_root.mkdir(parents=True)
    expected: set[str] = set()
    for index, extension in enumerate(guard.FRONTEND_TEST_EXTENSIONS):
        kind = "test" if index % 2 == 0 else "spec"
        relative = f"apps/control-center/src/example-{index}.{kind}.{extension}"
        (tmp_path / relative).write_text('test("covered", () => {});\n')
        expected.add(relative)

    assert set(guard.discover_test_files(tmp_path)) == expected


def test_discovery_covers_pytest_suffix_named_modules(tmp_path: Path) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    test_path = tests_root / "case_test.py"
    test_path.write_text("def test_suffix_style(): pass\n")

    assert guard._is_test_path("tests/case_test.py")
    assert guard.discover_test_files(tmp_path) == ("tests/case_test.py",)


def test_discovery_covers_vitest_defaults_outside_conventional_roots(
    tmp_path: Path,
) -> None:
    feature_root = tmp_path / "apps/control-center/features"
    feature_root.mkdir(parents=True)
    test_path = feature_root / "example.test.ts"
    test_path.write_text('test("covered", () => {});\n')
    ignored_root = tmp_path / "apps/control-center/node_modules/package"
    ignored_root.mkdir(parents=True)
    (ignored_root / "ignored.test.ts").write_text('test("ignored", () => {});\n')
    git_root = tmp_path / "apps/control-center/.git/internal"
    git_root.mkdir(parents=True)
    (git_root / "ignored.spec.ts").write_text('test("ignored", () => {});\n')
    extra_expected: list[str] = []
    for directory in ("build", "dist", "venv", ".cache"):
        relative = f"apps/control-center/{directory}/included.test.ts"
        target = tmp_path / relative
        target.parent.mkdir(parents=True)
        target.write_text('test("included", () => {});\n')
        extra_expected.append(relative)

    assert guard.discover_test_files(tmp_path) == tuple(
        sorted(("apps/control-center/features/example.test.ts", *extra_expected))
    )


def test_frontend_inventory_tracks_import_aliases_and_extended_apis() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.spec.ts",
        """
import { test as pw } from "@playwright/test";
const fixtureTest = pw.extend({ account: async ({}, use) => use("safe") });
pw("aliased test", () => {});
fixtureTest("extended test", () => {});
""",
    )

    assert declarations[0].ref == (
        "apps/control-center/src/example.spec.ts::aliased test"
    )
    assert declarations[1].ref.startswith(
        "apps/control-center/src/example.spec.ts::extended test::"
        "execution-test-extension:sha256:"
    )


def test_frontend_inventory_fails_closed_for_untracked_extended_api() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="extended test API cannot be inventoried safely",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.spec.ts",
            "const fixtureTest = test.extend<Fixtures>({});",
        )


@pytest.mark.parametrize(
    ("source", "message"),
    (
        (
            'const spec = test;\nspec("case", () => {});\n',
            "test API alias",
        ),
        (
            'const spec = test as typeof test;\nspec("case", () => {});\n',
            "test API alias",
        ),
        (
            'const spec = (test);\nspec("case", () => {});\n',
            "test API alias",
        ),
        (
            'const spec: typeof test = test;\nspec("case", () => {});\n',
            "test API alias",
        ),
        (
            'const spec = <typeof test>test;\nspec("case", () => {});\n',
            "test API alias",
        ),
        (
            'const spec = (<typeof test>test);\nspec("case", () => {});\n',
            "test API alias",
        ),
        (
            'const spec = ((<typeof test>test), test);\nspec("case", () => {});\n',
            "test API alias",
        ),
        (
            'const spec = (0, <typeof test>test);\nspec("case", () => {});\n',
            "test API alias",
        ),
        (
            "const spec = (0, <typeof test & { marker?: string; }>test);\n"
            'spec("case", () => {});\n',
            "test API alias",
        ),
        (
            "const spec = <ReturnType<() => typeof test>>test;\n"
            'spec("case", () => {});\n',
            "test API alias",
        ),
        (
            'const spec = enabled ? test : helper;\nspec("case", () => {});\n',
            "test API alias",
        ),
        (
            'const spec = (helper, test);\nspec("case", () => {});\n',
            "test API alias",
        ),
        (
            'const spec = (helper, test.only);\nspec("case", () => {});\n',
            "test API alias",
        ),
        (
            'const spec = test.bind(null);\nspec("case", () => {});\n',
            "test API alias",
        ),
        (
            "const spec = <typeof test & { marker?: string; }>test;\n"
            'spec("case", () => {});\n',
            "test API alias",
        ),
        (
            'const group = describe;\ngroup("suite", () => {});\n',
            "suite API alias",
        ),
    ),
)
def test_frontend_inventory_rejects_ordinary_runner_aliases(
    source: str,
    message: str,
) -> None:
    with pytest.raises(guard.TestCorpusGuardError, match=message):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.spec.ts",
            source,
        )


@pytest.mark.parametrize(
    "source",
    (
        "const { describe } = helpers;\ndescribe('suite', () => {});\n",
        "const [suite] = helpers;\nsuite('suite', () => {});\n",
        "const helper = (describe) => describe('suite', () => {});\n",
        "import { describe as group } from 'vitest';\n"
        "group.each([[1]])('suite %s', () => {});\n",
    ),
)
def test_frontend_inventory_rejects_shadowed_or_parameterized_suite_apis(
    source: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError, match="frontend (suite API|parameterized suites)"
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.spec.ts",
            source,
        )


def test_frontend_inventory_binds_identifiers_inside_literal_parameter_data() -> None:
    before = guard.parse_frontend_declarations(
        "apps/control-center/src/example.spec.ts",
        'const CASE_A = "one";\ntest.each([[CASE_A]])("case %s", () => {});\n',
    )
    after = guard.parse_frontend_declarations(
        "apps/control-center/src/example.spec.ts",
        'const CASE_A = "two";\ntest.each([[CASE_A]])("case %s", () => {});\n',
    )

    assert before[0].ref != after[0].ref


def test_frontend_inventory_rejects_hoisted_transitive_parameter_helpers() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="unproven transitive helper dependencies",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.spec.ts",
            "function buildCases() { return later(); }\n"
            "const cases = [buildCases()];\n"
            "function later() { return [[1], [2]]; }\n"
            'test.each(cases)("case %s", () => {});\n',
        )


def test_parameterized_frontend_inventory_rejects_missing_title() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="parameterized test title is missing",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            "it.each(cases);",
        )


def test_frontend_inventory_ignores_test_syntax_in_comments_and_strings() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        """
// it("commented out", () => {});
/* test.each(cases)("also commented out", () => {}); */
// globalThis["test"] = replacement;
const sample = 'it("string payload", () => {})';
const mutationSample = 'globalThis["test"] = replacement';
it("real declaration", () => {});
""",
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.test.tsx::real declaration",
    ]


def test_frontend_inventory_handles_escaped_title_quotes() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        r"""
it("renders \"quoted\" text", () => {});
test('rejects \'quoted\' input', () => {});
""",
    )

    assert [item.ref for item in declarations] == [
        'apps/control-center/src/example.test.tsx::renders "quoted" text',
        "apps/control-center/src/example.test.tsx::rejects 'quoted' input",
    ]


def test_frontend_inventory_rejects_dynamic_direct_test_titles() -> None:
    with pytest.raises(guard.TestCorpusGuardError, match="test title is invalid"):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.tsx",
            "it(dynamicTitle, () => {});",
        )


def test_frontend_inventory_ignores_playwright_conditional_skip_annotations() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/tests/example.spec.ts",
        """
test("declared test", async ({ page }) => {
  test.skip(testInfo.project.name !== "desktop", "desktop only");
});
""",
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/tests/example.spec.ts::declared test",
    ]


def test_removed_test_without_evidence_fails_closed() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="lack retirement/replacement evidence",
    ):
        _validate_retirements(
            {"tests/test_sample.py::test_replacement"},
            {"tests/test_sample.py::test_removed"},
            {"retirements": []},
        )


def test_retirement_requires_present_replacement_and_evidence() -> None:
    retired = "tests/test_sample.py::test_removed"
    replacement = "tests/test_sample.py::test_replacement"
    count = _validate_retirements(
        {replacement},
        {retired},
        {"retirements": [_record(retired, replacement)]},
    )

    assert count == 1


def test_retirement_with_missing_replacement_fails_closed() -> None:
    retired = "tests/test_sample.py::test_removed"
    with pytest.raises(guard.TestCorpusGuardError, match="missing replacements"):
        _validate_retirements(
            set(),
            {retired},
            {"retirements": [_record(retired, "tests/test_sample.py::test_missing")]},
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        (
            "assertion_equivalence_ref",
            "assertion-equivalence-ref:not-content-bound",
            "equivalence ref is invalid",
        ),
        (
            "evidence_ref",
            "test-corpus-evidence-ref:not-content-bound",
            "evidence ref is invalid",
        ),
        (
            "reason",
            "A substantive reason that includes\nunbounded lines.",
            "reason is too weak",
        ),
    ),
)
def test_retirement_metadata_must_be_bounded_and_content_bound(
    field: str,
    value: str,
    message: str,
) -> None:
    retired = "tests/test_sample.py::test_removed"
    replacement = "tests/test_sample.py::test_replacement"
    record = _record(retired, replacement)
    record[field] = value

    with pytest.raises(guard.TestCorpusGuardError, match=message):
        _validate_retirements(
            {replacement},
            {retired},
            {"retirements": [record]},
        )


@pytest.mark.parametrize(
    "unsafe_reason",
    (
        "Retirement evidence contains "
        + "/Us"
        + "ers/example/private/source material.",
        "Retirement evidence contains /workspace/ultimate-ai-agent/private.py.",
        "Retirement evidence contains /root/ultimate-ai-agent/private.py.",
        "Retirement evidence includes username from a local operator record.",
        "Retirement evidence includes api_"
        + "key="
        + "abcdefghijklmnop credential data.",
        "Retirement evidence includes a raw prompt from a prior run.",
    ),
)
def test_retirement_reason_rejects_sensitive_durable_content(
    unsafe_reason: str,
) -> None:
    retired = "tests/test_sample.py::test_removed"
    replacement = "tests/test_sample.py::test_replacement"
    record = _record(retired, replacement)
    record["reason"] = unsafe_reason

    with pytest.raises(guard.TestCorpusGuardError, match="reason is too weak"):
        _validate_retirements(
            {replacement},
            {retired},
            {"retirements": [record]},
        )


def test_retirement_reason_allows_safe_non_path_prose() -> None:
    retired = "tests/test_sample.py::test_removed"
    replacement = "tests/test_sample.py::test_replacement"
    record = _record(retired, replacement)
    record["reason"] = (
        "The replacement preserves the documented contract and exact defect class."
    )

    assert (
        _validate_retirements(
            {replacement},
            {retired},
            {"retirements": [record]},
        )
        == 1
    )


def test_retirement_records_reject_unknown_durable_fields() -> None:
    retired = "tests/test_sample.py::test_removed"
    replacement = "tests/test_sample.py::test_replacement"
    record = _record(retired, replacement)
    record["raw_output"] = "not allowed"

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="record fields are invalid",
    ):
        _validate_retirements(
            {replacement},
            {retired},
            {"retirements": [record]},
        )


def test_nested_retirement_evidence_is_content_bound() -> None:
    retired = "tests/test_sample.py::test_removed"
    replacement = "tests/test_sample.py::test_replacement"
    record = _record(retired, replacement)
    equivalence = record["assertion_equivalence_artifact"]
    assert isinstance(equivalence, dict)
    nested_records = equivalence["preserved_assertion_evidence"]
    assert isinstance(nested_records, list)
    nested = nested_records[0]
    assert isinstance(nested, dict)
    artifact = nested["artifact"]
    assert isinstance(artifact, dict)
    artifact["source_ref"] = f"test-source-ref:sha256:{'0' * 64}"
    record["assertion_equivalence_ref"] = guard.retirement_artifact_ref(
        "assertion-equivalence-ref", equivalence
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="preserved assertion evidence is invalid",
    ):
        _validate_retirements(
            {replacement},
            {retired},
            {"retirements": [record]},
        )


def test_retired_ref_must_use_a_supported_safe_test_path() -> None:
    replacement = "tests/test_sample.py::test_replacement"
    retired = "docs/not_a_test.txt::test_removed"

    with pytest.raises(guard.TestCorpusGuardError, match="retired test ref is invalid"):
        _validate_retirements(
            {replacement},
            {retired},
            {"retirements": [_record(retired, replacement)]},
        )


def test_retired_ref_requires_a_nonempty_declaration() -> None:
    replacement = "tests/test_sample.py::test_replacement"
    retired = "tests/test_sample.py::"

    with pytest.raises(guard.TestCorpusGuardError, match="retired test ref is invalid"):
        _validate_retirements(
            {replacement},
            {retired},
            {"retirements": [_record(retired, replacement)]},
        )


def test_retirement_ledger_rejects_symlinks_and_oversized_files(
    tmp_path: Path,
) -> None:
    ledger = tmp_path / guard.RETIREMENT_LEDGER
    ledger.parent.mkdir(parents=True)
    external = tmp_path / "external.json"
    external.write_text(
        '{"schema_version":"uaa.test_corpus_retirements.v1","retirements":[]}',
        encoding="utf-8",
    )
    ledger.symlink_to(external)

    with pytest.raises(guard.TestCorpusGuardError, match="ledger is unsafe"):
        guard._load_ledger(tmp_path)

    ledger.unlink()
    ledger.write_bytes(b" " * (guard.MAX_RETIREMENT_LEDGER_BYTES + 1))
    with pytest.raises(guard.TestCorpusGuardError, match="ledger is unsafe"):
        guard._load_ledger(tmp_path)


def test_worktree_inventory_reader_rejects_symlinks_and_hardlinks(
    tmp_path: Path,
) -> None:
    external = tmp_path / "external.py"
    external.write_text("def test_external(): pass\n", encoding="utf-8")
    symlink = tmp_path / "test_symlink.py"
    symlink.symlink_to(external)

    with pytest.raises(guard.TestCorpusGuardError, match="file is unsafe"):
        guard._read_worktree_text(tmp_path, symlink.name)

    hardlink = tmp_path / "test_hardlink.py"
    hardlink.hardlink_to(external)
    with pytest.raises(guard.TestCorpusGuardError, match="file is unsafe"):
        guard._read_worktree_text(tmp_path, hardlink.name)


def test_active_test_cannot_be_marked_retired() -> None:
    retired = "tests/test_sample.py::test_still_active"
    with pytest.raises(guard.TestCorpusGuardError, match="still active"):
        _validate_retirements(
            {retired},
            set(),
            {"retirements": [_record(retired, retired)]},
        )


def test_inventory_fingerprint_is_order_sensitive_and_content_free() -> None:
    first = (
        guard.TestDeclaration("tests/test_a.py::test_a", "python_test"),
        guard.TestDeclaration("tests/test_b.py::test_b", "python_test"),
    )
    second = tuple(reversed(first))

    assert guard.inventory_fingerprint(first) != guard.inventory_fingerprint(second)
    assert guard.inventory_fingerprint(first).startswith(
        "test-corpus-inventory-ref:sha256:"
    )


def test_repository_inventory_is_nonempty_and_deterministic() -> None:
    root = Path(__file__).resolve().parents[1]
    first = guard.inventory_worktree(root)
    second = guard.inventory_worktree(root)

    assert first == second
    assert len(first) > 1000
    assert {item.kind for item in first} == {"python_test", "frontend_test"}


def test_worktree_inventory_snapshot_reuses_exact_validated_declarations(
    tmp_path: Path,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "test_example.py").write_text("def test_case(): pass\n")

    snapshot = guard._inventory_worktree_snapshot(tmp_path)

    guard._validate_worktree_inventory_snapshot(
        tmp_path,
        snapshot,
        set(guard.discover_test_files(tmp_path)),
    )
    assert snapshot.declarations == guard.inventory_worktree(tmp_path)


def test_worktree_inventory_snapshot_rejects_changed_test_source(
    tmp_path: Path,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    target = tests_root / "test_example.py"
    target.write_text("def test_case(): pass\n")
    snapshot = guard._inventory_worktree_snapshot(tmp_path)
    target.write_text("def test_case(): assert False\n")

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="test inventory changed during verification",
    ):
        guard._validate_worktree_inventory_snapshot(
            tmp_path,
            snapshot,
            set(guard.discover_test_files(tmp_path)),
        )


def test_worktree_inventory_snapshot_rejects_changed_imported_source(
    tmp_path: Path,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "test_example.py").write_text(
        "import pytest\n"
        "from tests.helper import CASES\n"
        '@pytest.mark.parametrize("case", CASES)\n'
        "def test_case(case): pass\n"
    )
    helper = tests_root / "helper.py"
    helper.write_text("CASES = (1,)\n")
    snapshot = guard._inventory_worktree_snapshot(tmp_path)
    helper.write_text("CASES = (2,)\n")

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="test inventory changed during verification",
    ):
        guard._validate_worktree_inventory_snapshot(
            tmp_path,
            snapshot,
            set(guard.discover_test_files(tmp_path)),
        )


def test_worktree_inventory_snapshot_rejects_changed_frontend_imported_source(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "apps/control-center/src"
    source_root.mkdir(parents=True)
    test_path = source_root / "example.test.ts"
    test_path.write_text(
        'import { CASES } from "./cases";\ntest.each(CASES)("renders %s", () => {});\n'
    )
    helper = source_root / "cases.ts"
    helper.write_text('export const CASES = [["one"]] as const;\n')
    snapshot = guard._inventory_worktree_snapshot(tmp_path)
    helper.write_text('export const CASES = [["two"]] as const;\n')

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="test inventory changed during verification",
    ):
        guard._validate_worktree_inventory_snapshot(
            tmp_path,
            snapshot,
            set(guard.discover_test_files(tmp_path)),
        )


def test_removed_declarations_indexes_base_and_worktree_submodules(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_path = "tests/test_sample.py"
    package_path = "scripts/verification/__init__.py"
    module_path = "scripts/verification/ci_command_manifest.py"
    source = (
        "from scripts.verification import ci_command_manifest as manifest\n"
        "def test_case():\n"
        "    assert manifest.VALUE\n"
    )
    sources = {
        test_path: source,
        package_path: "",
        module_path: "VALUE = True\n",
    }
    for path, text in sources.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    monkeypatch.setattr(guard, "discover_test_files", lambda _repo: (test_path,))
    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base_sha: (test_path,),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset(sources),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, path: sources.get(path),
    )

    assert guard.removed_declarations(tmp_path, "a" * 40) == ()


def test_parameter_identity_migration_rejects_dependency_content_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_path = "tests/test_sample.py"
    data_path = "data.py"
    test_source = (
        "import pytest\n"
        "from data import Case\n"
        "@pytest.mark.parametrize('case', [Case()])\n"
        "def test_case(case): assert case.value\n"
    )
    base_data = "VALUE = 'before'\nclass Case:\n    def __init__(self): self.value = VALUE\n"
    current_data = (
        "VALUE = 'after'\nclass Case:\n    def __init__(self): self.value = VALUE\n"
    )
    for path, text in {test_path: test_source, data_path: current_data}.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    base_sources = {
        test_path: test_source,
        data_path: base_data,
        guard.TEST_CORPUS_GUARD_PATH: "legacy guard\n",
    }
    monkeypatch.setattr(guard, "discover_test_files", lambda _repo: (test_path,))
    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base_sha: (test_path,),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset(base_sources),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, path: base_sources.get(path),
    )

    assert guard.removed_declarations(tmp_path, "a" * 40)


def test_parameter_identity_migration_traverses_local_binding_chain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_path = "tests/test_sample.py"
    data_path = "data.py"
    test_source = (
        "import pytest\n"
        "from data import CASES\n"
        "PARAMS = CASES\n"
        "@pytest.mark.parametrize('case', PARAMS)\n"
        "def test_case(case): assert case\n"
    )
    base_data = "CASES = ('before',)\n"
    current_data = "CASES = ('after',)\n"
    for path, text in {test_path: test_source, data_path: current_data}.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    base_sources = {
        test_path: test_source,
        data_path: base_data,
        guard.TEST_CORPUS_GUARD_PATH: "legacy guard\n",
    }
    monkeypatch.setattr(guard, "discover_test_files", lambda _repo: (test_path,))
    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base_sha: (test_path,),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset(base_sources),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, path: base_sources.get(path),
    )

    assert guard.removed_declarations(tmp_path, "a" * 40)


def test_parameter_dependency_upgrade_does_not_hide_abort_posture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_path = "tests/test_sample.py"
    data_path = "data.py"
    test_source = (
        "import pytest\n"
        "from data import Case\n"
        "@pytest.mark.parametrize('case', [Case()])\n"
        "def test_case(case): assert case.value\n"
    )
    base_data = "class Case:\n    def __init__(self): self.value = True\n"
    current_data = (
        "import pytest\n"
        "class Case:\n"
        "    def __init__(self): pytest.skip('disabled')\n"
    )
    for path, text in {test_path: test_source, data_path: current_data}.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    base_sources = {
        test_path: test_source,
        data_path: base_data,
        guard.TEST_CORPUS_GUARD_PATH: "legacy guard\n",
    }
    monkeypatch.setattr(guard, "discover_test_files", lambda _repo: (test_path,))
    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base_sha: (test_path,),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset(base_sources),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, path: base_sources.get(path),
    )

    removed = guard.removed_declarations(tmp_path, "a" * 40)

    assert removed


def test_parameter_identity_migration_rejects_one_sided_local_dependency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_path = "tests/test_sample.py"
    data_path = "data.py"
    test_source = (
        "import pytest\n"
        "from data import CASES\n"
        "@pytest.mark.parametrize('case', CASES)\n"
        "def test_case(case): assert case\n"
    )
    target = tmp_path / test_path
    target.parent.mkdir(parents=True)
    target.write_text(test_source)
    base_sources = {
        test_path: test_source,
        data_path: "CASES = (True,)\n",
        guard.TEST_CORPUS_GUARD_PATH: "legacy guard\n",
    }
    monkeypatch.setattr(guard, "discover_test_files", lambda _repo: (test_path,))
    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base_sha: (test_path,),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset(base_sources),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, path: base_sources.get(path),
    )

    assert guard.removed_declarations(tmp_path, "a" * 40)


def test_parameter_identity_migration_approved_transition_is_exactly_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prior_ref = "tests/test_sample.py::test_case::parametrize-sha256:" + "a" * 64
    current_ref = "tests/test_sample.py::test_case::parametrize-sha256:" + "b" * 64
    source = "def test_case(): pass\n"
    base_dependency = "path=data.py\nVALUE = 'before'\n"
    current_dependency = "path=data.py\nVALUE = 'after'\n"
    monkeypatch.setattr(
        guard,
        "PARAMETER_DEPENDENCY_IDENTITY_MIGRATION_SOURCE_MODULE",
        "data",
    )
    monkeypatch.setattr(
        guard,
        "PARAMETER_DEPENDENCY_IDENTITY_MIGRATION_SOURCE_DIGESTS",
        (
            hashlib.sha256(base_dependency.encode()).hexdigest(),
            hashlib.sha256(current_dependency.encode()).hexdigest(),
        ),
    )
    monkeypatch.setattr(
        guard,
        "PARAMETER_DEPENDENCY_IDENTITY_MIGRATION_TRANSITIONS",
        {
            prior_ref: (
                current_ref,
                hashlib.sha256(source.encode()).hexdigest(),
            )
        },
    )

    assert guard._parameter_identity_migration_is_exact_approved_transition(
        prior_ref,
        current_ref,
        source,
        lambda module: base_dependency if module == "data" else None,
        lambda module: current_dependency if module == "data" else None,
    )
    assert not guard._parameter_identity_migration_is_exact_approved_transition(
        prior_ref,
        current_ref,
        source + "# changed\n",
        lambda module: base_dependency if module == "data" else None,
        lambda module: current_dependency if module == "data" else None,
    )
    assert not guard._parameter_identity_migration_is_exact_approved_transition(
        prior_ref,
        current_ref,
        source,
        lambda module: base_dependency if module == "data" else None,
        lambda module: "path=data.py\nVALUE = 'substituted'\n"
        if module == "data"
        else None,
    )


def test_removed_declarations_reuses_validated_python_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_path = "tests/test_sample.py"
    source = "def test_case(): pass\n"
    target = tmp_path / test_path
    target.parent.mkdir(parents=True)
    target.write_text(source)
    snapshot = guard._inventory_worktree_snapshot(tmp_path)
    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base_sha: (test_path,),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset({test_path}),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, path: source if path == test_path else None,
    )
    monkeypatch.setattr(
        guard,
        "_parse_worktree_test_declarations",
        lambda *_args, **_kwargs: pytest.fail(
            "validated Python declarations must be reused"
        ),
    )

    assert guard.removed_declarations(
        tmp_path,
        "a" * 40,
        worktree_snapshot=snapshot,
    ) == ()


def test_removed_declarations_reuses_validated_frontend_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_path = "apps/control-center/src/example.test.ts"
    source = 'test("case", () => {});\n'
    target = tmp_path / test_path
    target.parent.mkdir(parents=True)
    target.write_text(source)
    snapshot = guard._inventory_worktree_snapshot(tmp_path)
    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base_sha: (test_path,),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset({test_path}),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, path: source if path == test_path else None,
    )
    monkeypatch.setattr(
        guard,
        "_parse_worktree_test_declarations",
        lambda *_args, **_kwargs: pytest.fail(
            "validated frontend declarations must be reused"
        ),
    )

    assert (
        guard.removed_declarations(
            tmp_path,
            "a" * 40,
            worktree_snapshot=snapshot,
        )
        == ()
    )


def test_removed_declarations_revalidates_snapshot_after_changed_path_analysis(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_path = "tests/test_sample.py"
    source = "def test_case(): pass\n"
    target = tmp_path / test_path
    target.parent.mkdir(parents=True)
    target.write_text(source)
    snapshot = guard._inventory_worktree_snapshot(tmp_path)

    def mutate_during_changed_path_analysis(
        _repo: Path,
        _base_sha: str,
    ) -> tuple[str, ...]:
        target.write_text("def test_case(): assert False\n")
        return (test_path,)

    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        mutate_during_changed_path_analysis,
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset({test_path}),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, path: source if path == test_path else None,
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="test inventory changed during verification",
    ):
        guard.removed_declarations(
            tmp_path,
            "a" * 40,
            worktree_snapshot=snapshot,
        )


def test_removed_declarations_revalidates_snapshot_after_base_source_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_path = "tests/test_sample.py"
    package_path = "src/ultimate_ai_agent/__init__.py"
    module_path = "src/ultimate_ai_agent/subject.py"
    test_source = (
        "from ultimate_ai_agent.subject import runtime_value\n"
        "def test_case(): assert runtime_value()\n"
    )
    current_module_source = "def runtime_value(): return 'current'\n"
    current_sources = {
        test_path: test_source,
        package_path: "",
        module_path: current_module_source,
    }
    base_sources = {
        **current_sources,
        module_path: "def runtime_value(): return 'base'\n",
    }
    for path, text in current_sources.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    snapshot = guard._inventory_worktree_snapshot(tmp_path)

    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base_sha: (test_path,),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset(base_sources),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, path: base_sources.get(path),
    )
    original_read = guard._read_worktree_text
    module_reads = 0

    def mutate_during_base_source_revalidation(repo: Path, path: str) -> str:
        nonlocal module_reads
        source = original_read(repo, path)
        if path == module_path:
            module_reads += 1
            if module_reads == 2:
                (repo / test_path).write_text("def test_case(): assert False\n")
        return source

    monkeypatch.setattr(
        guard,
        "_read_worktree_text",
        mutate_during_base_source_revalidation,
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="test inventory changed during verification",
    ):
        guard.removed_declarations(
            tmp_path,
            "a" * 40,
            worktree_snapshot=snapshot,
        )


def test_removed_declarations_compares_base_application_parameter_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_path = "tests/test_sample.py"
    package_path = "src/ultimate_ai_agent/__init__.py"
    module_path = "src/ultimate_ai_agent/subject.py"
    test_source = (
        "import pytest\n"
        "from ultimate_ai_agent.subject import VALUES\n"
        "@pytest.mark.parametrize('value', VALUES)\n"
        "def test_case(value): assert value\n"
    )
    current_sources = {
        test_path: test_source,
        package_path: "",
        module_path: "VALUES = (1,)\n",
    }
    base_sources = {
        **current_sources,
        module_path: "VALUES = (1, 2)\n",
    }
    for path, text in current_sources.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    monkeypatch.setattr(guard, "discover_test_files", lambda _repo: (test_path,))
    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base_sha: (test_path,),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset(base_sources),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, path: base_sources.get(path),
    )

    removed = guard.removed_declarations(tmp_path, "a" * 40)

    assert len(removed) == 1
    assert removed[0].startswith(f"{test_path}::test_case::parametrize-sha256:")


def test_removed_declarations_reuses_collection_neutral_application_runtime_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_path = "tests/test_sample.py"
    package_path = "src/ultimate_ai_agent/__init__.py"
    module_path = "src/ultimate_ai_agent/subject.py"
    test_source = (
        "from ultimate_ai_agent.subject import runtime_value\n"
        "def test_case(): assert runtime_value()\n"
    )
    current_sources = {
        test_path: test_source,
        package_path: "",
        module_path: "def runtime_value(): return 'current'\n",
    }
    base_sources = {
        **current_sources,
        module_path: "def runtime_value(): return 'base'\n",
    }
    for path, text in current_sources.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    monkeypatch.setattr(guard, "discover_test_files", lambda _repo: (test_path,))
    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base_sha: (test_path,),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset(base_sources),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, path: base_sources.get(path),
    )

    assert guard.removed_declarations(tmp_path, "a" * 40) == ()


def test_removed_declarations_does_not_reuse_transitively_aborting_runtime_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_path = "tests/test_sample.py"
    package_path = "src/ultimate_ai_agent/__init__.py"
    module_path = "src/ultimate_ai_agent/subject.py"
    child_path = "src/ultimate_ai_agent/collection_child.py"
    test_source = (
        "from ultimate_ai_agent.subject import runtime_value\n"
        "def test_case(): assert runtime_value()\n"
    )
    base_sources = {
        test_path: test_source,
        package_path: "",
        module_path: "def runtime_value(): return 'base'\n",
        child_path: "VALUE = 'base'\n",
    }
    current_sources = {
        **base_sources,
        module_path: (
            "from ultimate_ai_agent.collection_child import VALUE\n"
            "def runtime_value(): return VALUE\n"
        ),
        child_path: (
            "import pytest\n"
            'pytest.skip("disabled", allow_module_level=True)\n'
            "VALUE = 'current'\n"
        ),
    }
    for path, text in current_sources.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    monkeypatch.setattr(guard, "discover_test_files", lambda _repo: (test_path,))
    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base_sha: (test_path,),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset(base_sources),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, path: base_sources.get(path),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="runtime import closure can abort collection",
    ):
        guard.removed_declarations(tmp_path, "a" * 40)


def test_removed_declarations_revalidates_current_sources_used_only_by_base_graph(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_path = "tests/test_sample.py"
    package_path = "src/ultimate_ai_agent/__init__.py"
    module_path = "src/ultimate_ai_agent/subject.py"
    base_test_source = (
        "from ultimate_ai_agent.subject import runtime_value\n"
        "def test_case(): assert runtime_value()\n"
    )
    current_test_source = "def test_case(): assert True\n"
    application_source = "def runtime_value(): return 'current'\n"
    base_sources = {
        test_path: base_test_source,
        package_path: "",
        module_path: "def runtime_value(): return 'base'\n",
    }
    current_sources = {
        test_path: current_test_source,
        package_path: "",
        module_path: application_source,
    }
    for path, text in current_sources.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    monkeypatch.setattr(guard, "discover_test_files", lambda _repo: (test_path,))
    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base_sha: (test_path,),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset(base_sources),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, path: base_sources.get(path),
    )
    original_read = guard._read_worktree_text
    mutated = False

    def mutate_after_base_only_read(repo: Path, path: str) -> str:
        nonlocal mutated
        source = original_read(repo, path)
        if path == module_path and not mutated:
            mutated = True
            (repo / path).write_text("def runtime_value(): return 'changed'\n")
        return source

    monkeypatch.setattr(guard, "_read_worktree_text", mutate_after_base_only_read)

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="test inventory changed during verification",
    ):
        guard.removed_declarations(tmp_path, "a" * 40)


def test_removed_declarations_reuses_nested_runtime_helper_application_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_path = "tests/test_sample.py"
    tests_package_path = "tests/__init__.py"
    helper_path = "tests/test_runtime_helper.py"
    package_path = "src/ultimate_ai_agent/__init__.py"
    module_path = "src/ultimate_ai_agent/subject.py"
    test_source = (
        "from .test_runtime_helper import runtime_helper\n"
        "def test_case(): assert runtime_helper()\n"
    )
    helper_source = (
        "from ultimate_ai_agent.subject import runtime_value\n"
        "def runtime_helper(): return runtime_value()\n"
    )
    current_sources = {
        test_path: test_source,
        tests_package_path: "",
        helper_path: helper_source,
        package_path: "",
        module_path: "def runtime_value(): return 'current'\n",
    }
    base_sources = {
        **current_sources,
        module_path: "def runtime_value(): return 'base'\n",
    }
    for path, text in current_sources.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    monkeypatch.setattr(guard, "discover_test_files", lambda _repo: (test_path,))
    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base_sha: (test_path,),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset(base_sources),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, path: base_sources.get(path),
    )

    assert guard.removed_declarations(tmp_path, "a" * 40) == ()


def test_removed_declarations_reuses_collection_neutral_autouse_runtime_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_path = "tests/test_sample.py"
    package_path = "src/ultimate_ai_agent/__init__.py"
    module_path = "src/ultimate_ai_agent/subject.py"
    test_source = (
        "import pytest\n"
        "from ultimate_ai_agent.subject import runtime_value\n"
        "@pytest.fixture(autouse=True)\n"
        "def runtime_fixture(): runtime_value()\n"
        "def test_case(): pass\n"
    )
    current_sources = {
        test_path: test_source,
        package_path: "",
        module_path: "def runtime_value(): return 'current'\n",
    }
    base_sources = {
        **current_sources,
        module_path: "def runtime_value(): return 'base'\n",
    }
    for path, text in current_sources.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    monkeypatch.setattr(guard, "discover_test_files", lambda _repo: (test_path,))
    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base_sha: (test_path,),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset(base_sources),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, path: base_sources.get(path),
    )

    assert guard.removed_declarations(tmp_path, "a" * 40) == ()


def test_removed_declarations_normalize_non_aborting_runtime_helper_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = "tests/test_sample.py"
    current = (
        "def prepare_value(): return 'current'\n"
        "def test_case(tmp_path): assert prepare_value()\n"
    )
    prior = (
        "def prepare_value(): return 'prior'\n"
        "def test_case(tmp_path): assert prepare_value()\n"
    )
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_text(current)
    monkeypatch.setattr(guard, "discover_test_files", lambda _repo: (path,))
    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base_sha: (path,),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset({path}),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, candidate: prior if candidate == path else None,
    )

    assert guard.removed_declarations(tmp_path, "a" * 40) == ()


def test_removed_declarations_bind_runtime_helper_abort_posture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = "tests/test_sample.py"
    current = (
        "import pytest\n"
        "def prepare_value(): pytest.skip('disabled')\n"
        "def test_case(tmp_path): assert prepare_value()\n"
    )
    prior = (
        "import pytest\n"
        "def prepare_value(): return 'enabled'\n"
        "def test_case(tmp_path): assert prepare_value()\n"
    )
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_text(current)
    monkeypatch.setattr(guard, "discover_test_files", lambda _repo: (path,))
    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base_sha: (path,),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset({path}),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, candidate: prior if candidate == path else None,
    )

    removed = guard.removed_declarations(tmp_path, "a" * 40)

    assert len(removed) == 1
    assert removed[0].startswith(f"{path}::test_case::parametrize-sha256:")


def test_removed_declarations_bind_parameter_data_during_helper_normalization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = "tests/test_sample.py"
    current = (
        "import pytest\n"
        "def prepare_value(): return 'current'\n"
        "@pytest.mark.parametrize('value', (2,))\n"
        "def test_case(value): assert prepare_value() and value\n"
    )
    prior = (
        "import pytest\n"
        "def prepare_value(): return 'prior'\n"
        "@pytest.mark.parametrize('value', (1,))\n"
        "def test_case(value): assert prepare_value() and value\n"
    )
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    target.write_text(current)
    monkeypatch.setattr(guard, "discover_test_files", lambda _repo: (path,))
    monkeypatch.setattr(
        guard,
        "_changed_test_paths",
        lambda _repo, _base_sha: (path,),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset({path}),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base_sha, candidate: prior if candidate == path else None,
    )

    removed = guard.removed_declarations(tmp_path, "a" * 40)

    assert len(removed) == 1
    assert removed[0].startswith(f"{path}::test_case::parametrize-sha256:")


def test_removed_declarations_bounds_base_module_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(guard, "MAX_PYTHON_DEPENDENCY_MODULES", 1)
    monkeypatch.setattr(guard, "discover_test_files", lambda _repo: ())
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base_sha: frozenset({"first.py", "second.py"}),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="base Python module index exceeds module budget",
    ):
        guard.removed_declarations(tmp_path, "a" * 40)


def test_malformed_requested_base_fails_closed() -> None:
    root = Path(__file__).resolve().parents[1]
    with pytest.raises(guard.TestCorpusGuardError, match="base SHA is malformed"):
        guard.verify_test_corpus_guard(root, base_sha="not-a-sha")


def test_requested_base_resolves_to_merge_base(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested = "a" * 40
    merge_base = "b" * 40
    commands: list[list[str]] = []

    def run_git(_repo: Path, args: list[str]) -> subprocess.CompletedProcess[bytes]:
        commands.append(args)
        stdout = f"{merge_base}\n".encode() if args[0] == "merge-base" else b""
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=stdout, stderr=b"")

    monkeypatch.setattr(guard, "_run_git", run_git)

    assert guard._resolve_base_sha(Path("."), requested) == merge_base
    assert commands == [
        ["cat-file", "-e", f"{requested}^{{commit}}"],
        ["merge-base", "HEAD", requested],
    ]


def test_requested_base_without_merge_base_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested = "a" * 40

    def run_git(_repo: Path, args: list[str]) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(
            args=args,
            returncode=1 if args[0] == "merge-base" else 0,
            stdout=b"",
            stderr=b"",
        )

    monkeypatch.setattr(guard, "_run_git", run_git)

    with pytest.raises(guard.TestCorpusGuardError, match="merge base is missing"):
        guard._resolve_base_sha(Path("."), requested)


def test_ci_without_canonical_base_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CI", "true")
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout=b"",
            stderr=b"",
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="canonical CI comparison base is missing",
    ):
        guard._resolve_base_sha(Path("."), None)


def test_malformed_canonical_ci_base_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=b"not-a-sha\n",
            stderr=b"",
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="canonical CI comparison base is malformed",
    ):
        guard._resolve_base_sha(Path("."), None)


@pytest.mark.parametrize(
    "path",
    (
        "tests/test_example.py",
        "apps/control-center/src/example.test.ts",
        "apps/control-center/src/example.test.tsx",
        "apps/control-center/src/example.spec.ts",
        "apps/control-center/src/example.spec.tsx",
        "apps/control-center/tests/example.spec.ts",
        "apps/control-center/tests/example.spec.tsx",
    ),
)
def test_supported_test_paths_cover_collector_suffixes(path: str) -> None:
    assert guard._is_test_path(path)


def test_python_discovery_matches_shard_runner_including_hidden_paths(
    tmp_path: Path,
) -> None:
    (tmp_path / "tests/.hidden").mkdir(parents=True)
    (tmp_path / "src/package").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / ".venv/lib").mkdir(parents=True)
    (tmp_path / "tests/test_visible.py").write_text("def test_case(): pass\n")
    (tmp_path / "tests/.hidden/test_hidden.py").write_text("def test_case(): pass\n")
    (tmp_path / "tests/example_test.py").write_text("def test_case(): pass\n")
    (tmp_path / "src/package/test_feature.py").write_text("def test_case(): pass\n")
    (tmp_path / "scripts/feature_test.py").write_text("def test_case(): pass\n")
    (tmp_path / ".venv/lib/test_ignored.py").write_text("def test_case(): pass\n")

    assert guard.discover_test_files(tmp_path) == (
        "tests/.hidden/test_hidden.py",
        "tests/example_test.py",
        "tests/test_visible.py",
    )


@pytest.mark.parametrize(
    "path",
    (
        "/tests/test_escape.py",
        "tests/../test_escape.py",
        "tests\\test_escape.py",
        "tests/test:escape.py",
        "tests/test_escape.py\nother",
    ),
)
def test_unsafe_changed_test_paths_fail_closed(path: str) -> None:
    with pytest.raises(guard.TestCorpusGuardError, match="path is unsafe"):
        guard._validate_test_path(path)


def test_changed_test_paths_reject_non_utf8_git_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=b"tests/test_bad_" + bytes([0xFF]) + b".py\0",
            stderr=b"",
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="paths are malformed",
    ):
        guard._changed_test_paths(Path("."), "a" * 40)


def test_base_file_paths_reject_non_utf8_git_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=b"tests/helper_" + bytes([0xFF]) + b".py\0",
            stderr=b"",
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="base repository paths are malformed",
    ):
        guard._base_file_paths(Path("."), "a" * 40)


def test_base_file_paths_parse_bounded_git_tree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[list[str]] = []

    def completed(
        _repo: Path,
        args: list[str],
    ) -> subprocess.CompletedProcess[bytes]:
        captured.append(args)
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=b"src/package.py\0tests/helper.py\0",
            stderr=b"",
        )

    monkeypatch.setattr(guard, "_run_git", completed)

    assert guard._base_file_paths(Path("."), "a" * 40) == frozenset(
        {"src/package.py", "tests/helper.py"}
    )
    assert captured == [["ls-tree", "-r", "--name-only", "-z", "a" * 40]]


def test_verifier_base_tree_snapshot_bounds_base_text_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[list[str]] = []

    def completed(
        _repo: Path,
        args: list[str],
    ) -> subprocess.CompletedProcess[bytes]:
        captured.append(args)
        output = (
            b"100644 blob "
            + (b"a" * 40)
            + b" 7\ttests/helper.py\0"
            if args[0] == "ls-tree"
            else b"content"
        )
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=output,
            stderr=b"",
        )

    monkeypatch.setattr(guard, "_run_git", completed)

    guard._load_base_tree_entries(Path("."), "b" * 40)
    assert guard._base_text(Path("."), "b" * 40, "tests/helper.py") == "content"
    assert captured == [
        ["ls-tree", "-r", "-l", "-z", "b" * 40],
        ["show", f"{'b' * 40}:tests/helper.py"],
    ]


def test_changed_test_paths_disable_rename_collapsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_args: list[list[str]] = []

    def completed(
        _repo: Path,
        args: list[str],
    ) -> subprocess.CompletedProcess[bytes]:
        captured_args.append(args)
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=b"tests/test_old.py\0tests/test_new.py\0",
            stderr=b"",
        )

    monkeypatch.setattr(guard, "_run_git", completed)
    monkeypatch.setattr(guard, "_base_text", lambda _repo, _base, _path: None)

    assert guard._changed_test_paths(Path("."), "a" * 40) == (
        "tests/test_new.py",
        "tests/test_old.py",
    )
    config_paths = [
        *sorted(guard.PYTEST_COLLECTION_CONFIG_PATHS),
        *sorted(guard.PYTEST_DEPENDENCY_LOCK_PATHS),
        *sorted(guard.PYTEST_RUNNER_CONFIG_PATHS),
        *sorted(guard.FRONTEND_COLLECTION_CONFIG_PATHS),
        *sorted(guard.FRONTEND_TEST_SCRIPT_CONFIG_PATHS),
    ]
    captured_change_args = [args for args in captured_args if args[0] != "ls-tree"]
    assert all(
        args[-len(config_paths) :] == config_paths for args in captured_change_args
    )
    captured_without_configs = [
        args[: -len(config_paths)] for args in captured_change_args
    ]
    source_paths = [
        "apps",
        guard.PYTHON_TEST_GIT_PATHSPEC,
        *guard.FRONTEND_SOURCE_GIT_PATHSPECS,
        *sorted(guard._pytest_runner_dependency_paths(Path("."))),
    ]
    assert captured_without_configs == [
        [
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            "a" * 40,
            "HEAD",
            "--",
            *source_paths,
        ],
        [
            "diff",
            "--cached",
            "--name-only",
            "--no-renames",
            "-z",
            "--",
            *source_paths,
        ],
        [
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            "--",
            *source_paths,
        ],
        [
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            *source_paths,
        ],
    ]


def test_changed_frontend_dataset_rechecks_importing_test(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_root = tmp_path / "apps/control-center/src"
    source_root.mkdir(parents=True)
    (source_root / "cases.ts").write_text('export const CASES = [["one"]] as const;\n')
    (source_root / "example.test.ts").write_text(
        'import { CASES } from "./cases";\ntest.each(CASES)("renders %s", () => {});\n'
    )
    outputs = iter(
        (
            b"apps/control-center/src/cases.ts\0",
            b"",
            b"",
            b"",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=next(outputs),
            stderr=b"",
        ),
    )

    assert guard._changed_test_paths(tmp_path, "a" * 40) == (
        "apps/control-center/src/example.test.ts",
    )


@pytest.mark.parametrize(
    "runtime_edge",
    (
        'import "./state";',
        'const state = require("./state"); void state;',
        'void import("./state");',
        'export * as state from "./state";',
    ),
)
def test_changed_transitive_frontend_initializer_rechecks_importing_test(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    runtime_edge: str,
) -> None:
    source_root = tmp_path / "apps/control-center/src"
    source_root.mkdir(parents=True)
    (source_root / "state.ts").write_text("export const state = 'one';\n")
    (source_root / "helper.ts").write_text(
        f"{runtime_edge}\n"
        'import { beforeEach } from "vitest";\n'
        "beforeEach(context => context.skip());\n"
        "export const UNUSED = 'bound';\n"
    )
    (source_root / "example.test.ts").write_text(
        'import { UNUSED } from "./helper";\ntest("case", () => {});\n'
    )
    outputs = iter((b"apps/control-center/src/state.ts\0", b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    assert guard._changed_test_paths(tmp_path, "a" * 40) == (
        "apps/control-center/src/example.test.ts",
    )


def test_frontend_runtime_dependency_cache_preserves_cycle_closure() -> None:
    sources = {
        "a.ts": 'import "./b";\n',
        "b.ts": 'import "./c";\nimport "./d";\n',
        "c.ts": 'import "./b";\n',
        "d.ts": "export const value = true;\n",
    }
    cache: dict[str, frozenset[str]] = {}

    first = guard._frontend_runtime_dependency_paths(
        {"a.ts"},
        sources.get,
        cache,
    )
    second = guard._frontend_runtime_dependency_paths(
        {"c.ts"},
        sources.get,
        cache,
    )

    assert {"b.ts", "c.ts", "d.ts"} <= first
    assert {"b.ts", "c.ts", "d.ts"} <= second


def test_changed_repository_frontend_dataset_rechecks_importing_test(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_root = tmp_path / "apps/control-center/src"
    source_root.mkdir(parents=True)
    shared_root = tmp_path / "shared"
    shared_root.mkdir(parents=True)
    (shared_root / "cases.ts").write_text('export const CASES = [["one"]] as const;\n')
    (source_root / "example.test.ts").write_text(
        'import { CASES } from "../../../shared/cases";\n'
        'test.each(CASES)("renders %s", () => {});\n'
    )
    outputs = iter((b"shared/cases.ts\0", b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    assert guard._changed_test_paths(tmp_path, "a" * 40) == (
        "apps/control-center/src/example.test.ts",
    )


def test_python_inventory_binds_imported_parameter_module_source(
    tmp_path: Path,
) -> None:
    scripts_root = tmp_path / "scripts"
    scripts_root.mkdir()
    source_path = scripts_root / "data.py"
    source_path.write_text('CASES = ["one", "two"]\n')
    test_text = """
import pytest
from scripts import data

@pytest.mark.parametrize("value", data.CASES)
def test_case(value):
    assert value
"""
    before = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )
    source_path.write_text('CASES = ["one"]\n')
    after = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )

    assert before[0].ref != after[0].ref


def test_python_inventory_binds_from_imported_parameter_module_source(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "data.py"
    source_path.write_text('CASES = ["one", "two"]\n')
    test_text = """
import pytest
from data import CASES

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value
"""
    before = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )
    source_path.write_text('CASES = ["one"]\n')
    after = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )

    assert before[0].ref != after[0].ref


def test_python_inventory_binds_imported_parameterized_fixture_source(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "fixtures.py"
    source_path.write_text(
        "import pytest\n"
        "@pytest.fixture(params=[1, 2])\n"
        "def value(request): return request.param\n"
    )
    test_text = "from fixtures import value\ndef test_case(value): assert value\n"
    before = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )
    source_path.write_text(
        "import pytest\n"
        "@pytest.fixture(params=[1])\n"
        "def value(request): return request.param\n"
    )
    after = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )

    assert before[0].ref != after[0].ref


def test_python_inventory_binds_imported_parameter_id_helper(tmp_path: Path) -> None:
    source_path = tmp_path / "data.py"
    source_path.write_text('def make_id(value):\n    return f"before-{value}"\n')
    test_text = """
import pytest
from data import make_id

@pytest.mark.parametrize("value", ["one"], ids=make_id)
def test_case(value):
    assert value
"""
    before = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )
    source_path.write_text('def make_id(value):\n    return f"after-{value}"\n')
    after = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )

    assert before[0].ref != after[0].ref


def test_python_source_ref_binds_imported_parameter_module_source(
    tmp_path: Path,
) -> None:
    (tmp_path / "tests").mkdir()
    source_path = tmp_path / "data.py"
    source_path.write_text('CASES = ["one", "two"]\n')
    test_path = tmp_path / "tests/test_sample.py"
    test_path.write_text(
        "import pytest\n"
        "from data import CASES\n"
        '@pytest.mark.parametrize("value", CASES)\n'
        "def test_case(value): assert value\n"
    )

    before_ref = guard._parse_worktree_test_declarations(
        tmp_path,
        "tests/test_sample.py",
        test_path.read_text(),
    )[0].ref
    before_source_ref = guard._worktree_source_ref(tmp_path, before_ref)

    source_path.write_text('CASES = ["one"]\n')
    after_ref = guard._parse_worktree_test_declarations(
        tmp_path,
        "tests/test_sample.py",
        test_path.read_text(),
    )[0].ref
    after_source_ref = guard._worktree_source_ref(tmp_path, after_ref)

    assert before_ref != after_ref
    assert before_source_ref != after_source_ref


def test_python_inventory_rejects_class_body_parameter_data() -> None:
    source = """
import pytest

class TestExample:
    CASES = [1, 2]

    @pytest.mark.parametrize("value", CASES)
    def test_case(self, value):
        assert value
"""

    with pytest.raises(guard.TestCorpusGuardError, match="class-body"):
        guard.parse_python_declarations("tests/test_sample.py", source)


def test_python_inventory_rejects_wildcard_parameter_imports() -> None:
    source = """
import pytest
from scripts.data import *

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value
"""

    with pytest.raises(guard.TestCorpusGuardError, match="wildcard"):
        guard.parse_python_declarations("tests/test_sample.py", source)


def test_python_inventory_rejects_repository_file_parameter_data(
    tmp_path: Path,
) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "data.py").write_text(
        "import json\n"
        "from pathlib import Path\n"
        'CASES = json.loads(Path("scripts/cases.json").read_text())\n'
    )
    test_text = (
        "import pytest\n"
        "from data import CASES\n"
        '@pytest.mark.parametrize("value", CASES)\n'
        "def test_case(value): pass\n"
    )

    with pytest.raises(guard.TestCorpusGuardError, match="repository-file"):
        guard._parse_worktree_test_declarations(
            tmp_path, "tests/test_sample.py", test_text
        )


@pytest.mark.parametrize(
    "source",
    (
        "import json\n"
        "from pathlib import Path\n"
        "import pytest\n"
        'CASES = json.loads(Path("tests/cases.json").read_text())\n'
        '@pytest.mark.parametrize("value", CASES)\n'
        "def test_case(value): pass\n",
        "from pathlib import Path\n"
        "import pytest\n"
        "class Cases:\n"
        "    def __init__(self):\n"
        '        self.values = Path("tests/cases.json").read_text()\n'
        "CASES = Cases()\n"
        '@pytest.mark.parametrize("value", CASES)\n'
        "def test_case(value): pass\n",
        "from pathlib import Path\n"
        "import pytest\n"
        "def load_cases():\n"
        '    return Path("tests/cases.json").read_text()\n'
        '@pytest.mark.parametrize("value", load_cases())\n'
        "def test_case(value): pass\n",
        "from pathlib import Path\n"
        "import pytest\n"
        'CASES = list(Path("tests/cases").glob("*.json"))\n'
        '@pytest.mark.parametrize("value", CASES)\n'
        "def test_case(value): pass\n",
    ),
)
def test_python_inventory_rejects_local_repository_file_parameter_data(
    source: str,
) -> None:
    with pytest.raises(guard.TestCorpusGuardError, match="repository-file"):
        guard.parse_python_declarations("tests/test_sample.py", source)


def test_python_inventory_binds_imported_parametrize_argnames(tmp_path: Path) -> None:
    scripts_root = tmp_path / "scripts"
    scripts_root.mkdir()
    source_path = scripts_root / "data.py"
    source_path.write_text('ARGNAMES = "value"\n')
    (tmp_path / "tests").mkdir()
    test_text = (
        "import pytest\n"
        "from scripts.data import ARGNAMES\n"
        "@pytest.mark.parametrize(ARGNAMES, [(1,)])\n"
        "def test_case(value): pass\n"
    )
    before = guard._parse_worktree_test_declarations(
        tmp_path,
        "tests/test_sample.py",
        test_text,
    )
    source_path.write_text('ARGNAMES = "other"\n')
    after = guard._parse_worktree_test_declarations(
        tmp_path,
        "tests/test_sample.py",
        test_text,
    )

    assert before[0].ref != after[0].ref


def test_python_inventory_rejects_aliased_repository_file_reader(
    tmp_path: Path,
) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "data.py").write_text(
        "import json\n"
        "reader = open\n"
        "def load_cases():\n"
        '    with reader("scripts/cases.json") as handle:\n'
        "        return json.load(handle)\n"
        "CASES = load_cases()\n"
    )
    test_text = (
        "import pytest\n"
        "from data import CASES\n"
        '@pytest.mark.parametrize("value", CASES)\n'
        "def test_case(value): pass\n"
    )

    with pytest.raises(guard.TestCorpusGuardError, match="repository-file"):
        guard._parse_worktree_test_declarations(
            tmp_path, "tests/test_sample.py", test_text
        )


@pytest.mark.parametrize("module", ["builtins", "io"])
def test_python_inventory_rejects_import_aliased_repository_file_reader(
    tmp_path: Path,
    module: str,
) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "data.py").write_text(
        "import json\n"
        f"from {module} import open as reader\n"
        "def load_cases():\n"
        '    with reader("scripts/cases.json") as handle:\n'
        "        return json.load(handle)\n"
        "CASES = load_cases()\n"
    )
    test_text = (
        "import pytest\n"
        "from data import CASES\n"
        '@pytest.mark.parametrize("value", CASES)\n'
        "def test_case(value): pass\n"
    )

    with pytest.raises(guard.TestCorpusGuardError, match="repository-file"):
        guard._parse_worktree_test_declarations(
            tmp_path, "tests/test_sample.py", test_text
        )


def test_changed_python_dataset_rechecks_importing_test(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/data.py").write_text('CASES = ["one"]\n')
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_sample.py").write_text(
        "import pytest\n"
        "from scripts import data\n"
        '@pytest.mark.parametrize("value", data.CASES)\n'
        "def test_case(value): pass\n"
    )
    outputs = iter((b"scripts/data.py\0", b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    assert guard._changed_test_paths(tmp_path, "a" * 40) == ("tests/test_sample.py",)


@pytest.mark.parametrize(
    ("current", "prior"),
    (
        (
            "import pytest\npytest.skip('disabled', allow_module_level=True)\n",
            "",
        ),
        (
            "",
            "import pytest\npytest.skip('disabled', allow_module_level=True)\n",
        ),
        (
            "import unittest\nraise unittest.SkipTest('disabled')\n",
            "",
        ),
    ),
)
def test_changed_python_package_initializer_collection_abort_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    current: str,
    prior: str,
) -> None:
    package = tmp_path / "tests/pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(current)
    (package / "test_sample.py").write_text("def test_case(): pass\n")
    outputs = iter((b"tests/pkg/__init__.py\0", b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: prior if path == "tests/pkg/__init__.py" else None,
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="package initializer collection abort",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_python_package_initializer_rechecks_package_tests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = tmp_path / "tests/pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("PACKAGE_MODE = 'current'\n")
    (package / "test_sample.py").write_text("def test_case(): pass\n")
    outputs = iter((b"tests/pkg/__init__.py\0", b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(guard, "_base_text", lambda _repo, _base, _path: None)

    assert guard._changed_test_paths(tmp_path, "a" * 40) == (
        "tests/pkg/test_sample.py",
    )


def test_changed_transitive_python_dataset_rechecks_importing_test(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/data.py").write_text(
        "from scripts.helpers import build_cases\nCASES = build_cases()\n"
    )
    (tmp_path / "scripts/helpers.py").write_text(
        'def build_cases():\n    return ["one"]\n'
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_sample.py").write_text(
        "import pytest\n"
        "from scripts.data import CASES\n"
        '@pytest.mark.parametrize("value", CASES)\n'
        "def test_case(value): pass\n"
    )
    outputs = iter((b"scripts/helpers.py\0", b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    assert guard._changed_test_paths(tmp_path, "a" * 40) == ("tests/test_sample.py",)


@pytest.mark.parametrize(
    ("data_source", "test_import"),
    (
        (
            "def build_cases():\n"
            "    from scripts.helpers import CASES\n"
            "    return CASES\n"
            "CASES = build_cases()\n",
            "from scripts.data import CASES\n",
        ),
        (
            'CASES = ["one"]\n',
            "from scripts.data import *\n",
        ),
    ),
)
def test_changed_nested_or_wildcard_python_dataset_rechecks_importing_test(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    data_source: str,
    test_import: str,
) -> None:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/data.py").write_text(data_source)
    (tmp_path / "scripts/helpers.py").write_text('CASES = ["one"]\n')
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_sample.py").write_text(
        "import pytest\n"
        + test_import
        + '@pytest.mark.parametrize("value", CASES)\n'
        + "def test_case(value): pass\n"
    )
    changed_path = (
        b"scripts/helpers.py\0" if "helpers" in data_source else b"scripts/data.py\0"
    )
    outputs = iter((changed_path, b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    assert guard._changed_test_paths(tmp_path, "a" * 40) == ("tests/test_sample.py",)


def test_changed_lazy_export_python_dataset_rechecks_importing_test(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = tmp_path / "scripts/catalog"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('_LAZY_EXPORT_MODULES = {"CASES": ".data"}\n')
    (package / "data.py").write_text('CASES = ["one"]\n')
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_sample.py").write_text(
        "import pytest\n"
        "from scripts.catalog import CASES\n"
        '@pytest.mark.parametrize("value", CASES)\n'
        "def test_case(value): pass\n"
    )
    outputs = iter((b"scripts/catalog/data.py\0", b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    assert guard._changed_test_paths(tmp_path, "a" * 40) == ("tests/test_sample.py",)


def test_changed_pytest_collection_configuration_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = '[tool.pytest.ini_options]\npython_functions = ["check_*"]\n'
    prior = '[tool.pytest.ini_options]\npython_functions = ["test_*"]\n'
    (tmp_path / "pyproject.toml").write_text(current)
    outputs = iter(
        (
            b"pyproject.toml\0",
            b"",
            b"",
            b"",
            str(len(prior.encode())).encode(),
            prior.encode(),
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    with pytest.raises(guard.TestCorpusGuardError, match="collection configuration"):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_pytest11_entry_point_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = '[project.entry-points."pytest11"]\nlocal = "tests.plugin"\n'
    prior = "[project]\nname = 'sample'\n"
    (tmp_path / "pyproject.toml").write_text(current)
    outputs = iter(
        (
            b"pyproject.toml\0",
            b"",
            b"",
            b"",
            str(len(prior.encode())).encode(),
            prior.encode(),
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    with pytest.raises(guard.TestCorpusGuardError, match="entry-point configuration"):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_pytest_dev_dependency_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = '[project.optional-dependencies]\ndev = ["pytest", "sample-plugin"]\n'
    prior = '[project.optional-dependencies]\ndev = ["pytest"]\n'
    (tmp_path / "pyproject.toml").write_text(current)
    outputs = iter(
        (
            b"pyproject.toml\0",
            b"",
            b"",
            b"",
            str(len(prior.encode())).encode(),
            prior.encode(),
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="pytest dependency configuration",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_pytest_dependency_lock_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "uv.lock").write_text("version = 1\n")
    outputs = iter((b"uv.lock\0", b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="pytest dependency lock",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


@pytest.mark.parametrize("config_path", sorted(guard.PYTEST_RUNNER_CONFIG_PATHS))
def test_changed_pytest_runner_configuration_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    config_path: str,
) -> None:
    current = "RUNNER_CONFIGURATION = 'current'\n"
    prior = "RUNNER_CONFIGURATION = 'prior'\n"
    target = tmp_path / config_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(current)
    outputs = iter(
        (
            f"{config_path}\0".encode(),
            b"",
            b"",
            b"",
            str(len(prior.encode())).encode(),
            prior.encode(),
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="pytest runner configuration",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_exact_pytest_suffix_discovery_alignment_is_bounded() -> None:
    manifest_path = "scripts/verification/ci_command_manifest.py"
    runner_path = "scripts/verification/run_pytest_shards.py"
    prior_manifest = (
        'patterns = (\n                    "tests/**/test_*.py",\n)\n'
        '                    "--hard-timeout-seconds",\n'
        '                    "1800",\n'
        '                    "--quiet",\n'
        '                    "--safe-summary",\n'
        "                ),\n"
        '                (),\n'
        '                "test",\n'
        "                1830,\n"
        "            ),\n"
        '                    "{temp_root}/uaa_static_verification_timings.json",\n'
        "                ),\n"
        '                (),\n'
        '                "verification",\n'
        "                900,\n"
        "            ),\n"
    )
    current_manifest = prior_manifest.replace(
        '                    "tests/**/test_*.py",\n',
        '                    "tests/**/test_*.py",\n'
        '                    "tests/**/*_test.py",\n',
    )
    prior_runner = (
        "def discover_test_files(root):\n"
        "    return sorted(\n"
        '        for path in (root / "tests").rglob("test_*.py")\n'
        "        if path.is_file()\n"
        "    )\n"
        "if not files:\n"
        '        print("FAIL: no tests/test_*.py files discovered", file=sys.stderr)\n'
    )
    current_runner = prior_runner.replace(
        '        for path in (root / "tests").rglob("test_*.py")\n'
        "        if path.is_file()\n",
        '        for path in (root / "tests").rglob("*.py")\n'
        "        if path.is_file()\n"
        '        and (path.name.startswith("test_") or path.name.endswith("_test.py"))\n',
    ).replace(
        '        print("FAIL: no tests/test_*.py files discovered", file=sys.stderr)\n',
        '        print("FAIL: no canonical Python test files discovered", file=sys.stderr)\n',
    )

    aligned = guard._safe_pytest_suffix_discovery_alignment_paths(
        current_by_path={
            manifest_path: current_manifest,
            runner_path: current_runner,
        },
        prior_by_path={
            manifest_path: prior_manifest,
            runner_path: prior_runner,
        },
    )

    assert aligned == {manifest_path, runner_path}
    aligned_with_static_timeout = guard._safe_pytest_suffix_discovery_alignment_paths(
        current_by_path={
            manifest_path: current_manifest.replace(
                "                900,\n",
                "                1_800,\n",
            ),
            runner_path: current_runner,
        },
        prior_by_path={
            manifest_path: prior_manifest,
            runner_path: prior_runner,
        },
    )

    assert aligned_with_static_timeout == {manifest_path, runner_path}
    aligned_with_pytest_timeout_change = guard._safe_pytest_suffix_discovery_alignment_paths(
        current_by_path={
            manifest_path: current_manifest.replace(
                '                    "1800",\n',
                '                    "2050",\n',
            ).replace(
                "                1830,\n",
                "                2080,\n",
            ).replace(
                "                900,\n",
                "                1_800,\n",
            ),
            runner_path: current_runner,
        },
        prior_by_path={
            manifest_path: prior_manifest,
            runner_path: prior_runner,
        },
    )

    assert not aligned_with_pytest_timeout_change
    assert not guard._safe_pytest_suffix_discovery_alignment_paths(
        current_by_path={
            manifest_path: current_manifest.replace(
                '                    "1800",\n',
                '                    "2051",\n',
            ).replace(
                "                1830,\n",
                "                2080,\n",
            ),
            runner_path: current_runner,
        },
        prior_by_path={
            manifest_path: prior_manifest,
            runner_path: prior_runner,
        },
    )
    assert not guard._safe_pytest_suffix_discovery_alignment_paths(
        current_by_path={
            manifest_path: current_manifest.replace(
                "                900,\n",
                "                1_801,\n",
            ),
            runner_path: current_runner,
        },
        prior_by_path={
            manifest_path: prior_manifest,
            runner_path: prior_runner,
        },
    )
    assert not guard._safe_pytest_suffix_discovery_alignment_paths(
        current_by_path={
            manifest_path: current_manifest,
            runner_path: current_runner + "# unrelated runner change\n",
        },
        prior_by_path={
            manifest_path: prior_manifest,
            runner_path: prior_runner,
        },
    )
    assert not guard._safe_pytest_suffix_discovery_alignment_paths(
        current_by_path={manifest_path: current_manifest},
        prior_by_path={manifest_path: prior_manifest},
    )


def test_exact_performance_runner_evidence_alignment_is_pair_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner_path = guard.PERFORMANCE_RUNNER_ALIGNMENT_PATH
    prior = "def run_lane():\n    return 'prior'\n"
    current = "def run_lane():\n    return 'performance-evidence-v1'\n"
    monkeypatch.setattr(
        guard,
        "PERFORMANCE_RUNNER_APPROVED_PRIOR_SHA256",
        hashlib.sha256(prior.encode()).hexdigest(),
    )
    monkeypatch.setattr(
        guard,
        "PERFORMANCE_RUNNER_APPROVED_CURRENT_SHA256",
        hashlib.sha256(current.encode()).hexdigest(),
    )

    assert guard._safe_performance_runner_evidence_alignment_paths(
        current_by_path={runner_path: current},
        prior_by_path={runner_path: prior},
    ) == {runner_path}
    assert not guard._safe_performance_runner_evidence_alignment_paths(
        current_by_path={runner_path: current + "PYTEST_ADDOPTS = '--deselect=x'\n"},
        prior_by_path={runner_path: prior},
    )
    assert not guard._safe_performance_runner_evidence_alignment_paths(
        current_by_path={runner_path: current},
        prior_by_path={runner_path: prior + "# different base\n"},
    )
    assert not guard._safe_performance_runner_evidence_alignment_paths(
        current_by_path={
            runner_path: current,
            ".github/workflows/ci.yml": "pytest: changed\n",
        },
        prior_by_path={
            runner_path: prior,
            ".github/workflows/ci.yml": "pytest: prior\n",
        },
    )


def test_changed_test_paths_accepts_exact_performance_runner_alignment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner_path = guard.PERFORMANCE_RUNNER_ALIGNMENT_PATH
    prior = "def run_lane():\n    return 'prior'\n"
    current = "def run_lane():\n    return 'performance-evidence-v1'\n"
    target = tmp_path / runner_path
    target.parent.mkdir(parents=True)
    target.write_text(current, encoding="utf-8")
    monkeypatch.setattr(
        guard,
        "PERFORMANCE_RUNNER_APPROVED_PRIOR_SHA256",
        hashlib.sha256(prior.encode()).hexdigest(),
    )
    monkeypatch.setattr(
        guard,
        "PERFORMANCE_RUNNER_APPROVED_CURRENT_SHA256",
        hashlib.sha256(current.encode()).hexdigest(),
    )
    outputs = iter(
        (
            f"{runner_path}\0".encode(),
            b"",
            b"",
            b"",
            str(len(prior.encode())).encode(),
            prior.encode(),
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    assert guard._changed_test_paths(tmp_path, "a" * 40) == ()


def test_approved_performance_runner_current_fingerprint_is_exact() -> None:
    runner_path = guard.PERFORMANCE_RUNNER_ALIGNMENT_PATH
    current = (Path(__file__).parents[1] / runner_path).read_bytes()

    assert hashlib.sha256(current).hexdigest() == (
        guard.PERFORMANCE_RUNNER_APPROVED_CURRENT_SHA256
    )


@pytest.mark.parametrize(
    "changed_path",
    (
        "scripts/verification/collection_helper.py",
        "scripts/verification/__init__.py",
    ),
)
def test_changed_pytest_runner_dependency_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    changed_path: str,
) -> None:
    verification = tmp_path / "scripts/verification"
    verification.mkdir(parents=True)
    (verification / "pytest_collection_evidence.py").write_text(
        "from scripts.verification import collection_helper\n"
    )
    (verification / "collection_helper.py").write_text(
        "def pytest_collection_modifyitems(items): items.clear()\n"
    )
    (verification / "__init__.py").write_text("")
    outputs = iter((f"{changed_path}\0".encode(), b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="pytest runner dependency",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_pytest_shard_runner_helper_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verification = tmp_path / "scripts/verification"
    verification.mkdir(parents=True)
    (verification / "run_pytest_shards.py").write_text(
        "from scripts.verification import pytest_shard_processes\n"
    )
    (verification / "pytest_shard_processes.py").write_text(
        "def build_shard_env(): "
        "return {'PYTEST_ADDOPTS': '--deselect=tests/test_target.py'}\n"
    )
    (verification / "__init__.py").write_text("")
    changed_path = "scripts/verification/pytest_shard_processes.py"
    outputs = iter((f"{changed_path}\0".encode(), b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="pytest runner dependency",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_canonical_lane_wrapper_helper_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verification = tmp_path / "scripts/verification"
    verification.mkdir(parents=True)
    (verification / "run_ci_lane.py").write_text(
        "from scripts.verification import ci_lane_helper\n"
    )
    (verification / "ci_lane_helper.py").write_text(
        "def execute_lane(): return 'command:pytest.sharded-suite'\n"
    )
    (verification / "__init__.py").write_text("")
    changed_path = "scripts/verification/ci_lane_helper.py"
    outputs = iter((f"{changed_path}\0".encode(), b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="pytest runner dependency",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_commented_pyproject_collection_header_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = '[tool.pytest.ini_options] # collection\npython_functions = ["check_*"]\n'
    prior = '[tool.pytest.ini_options] # collection\npython_functions = ["test_*"]\n'
    (tmp_path / "pyproject.toml").write_text(current)
    outputs = iter(
        (
            b"pyproject.toml\0",
            b"",
            b"",
            b"",
            str(len(prior.encode())).encode(),
            prior.encode(),
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    with pytest.raises(guard.TestCorpusGuardError, match="collection configuration"):
        guard._changed_test_paths(tmp_path, "a" * 40)


@pytest.mark.parametrize("config_path", ("pytest.toml", ".pytest.toml", ".pytest.ini"))
def test_changed_additional_pytest_collection_configuration_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    config_path: str,
) -> None:
    current = "[pytest]\npython_functions = 'check_*'\n"
    prior = "[pytest]\npython_functions = 'test_*'\n"
    (tmp_path / config_path).write_text(current)
    outputs = iter(
        (
            f"{config_path}\0".encode(),
            b"",
            b"",
            b"",
            str(len(prior.encode())).encode(),
            prior.encode(),
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    with pytest.raises(guard.TestCorpusGuardError, match="collection configuration"):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_setup_cfg_pytest_collection_configuration_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = "[tool:pytest]\npython_functions = check_*\n"
    prior = "[tool:pytest]\npython_functions = test_*\n"
    (tmp_path / "setup.cfg").write_text(current)
    outputs = iter(
        (
            b"setup.cfg\0",
            b"",
            b"",
            b"",
            str(len(prior.encode())).encode(),
            prior.encode(),
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    with pytest.raises(guard.TestCorpusGuardError, match="collection configuration"):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_every_changed_tox_configuration_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = "[testenv]\ncommands = pytest tests/test_new.py\n"
    prior = "[testenv]\ncommands = pytest tests/test_old.py\n"
    (tmp_path / "tox.ini").write_text(current)
    outputs = iter(
        (
            b"tox.ini\0",
            b"",
            b"",
            b"",
            str(len(prior.encode())).encode(),
            prior.encode(),
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    with pytest.raises(guard.TestCorpusGuardError, match="collection configuration"):
        guard._changed_test_paths(tmp_path, "a" * 40)


@pytest.mark.parametrize(
    "config_path",
    sorted(guard.FRONTEND_COLLECTION_CONFIG_PATHS),
)
def test_changed_frontend_collection_configuration_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    config_path: str,
) -> None:
    current = 'export default { test: { exclude: ["tests/visual/**"] } };\n'
    prior = "export default { test: { exclude: [] } };\n"
    target = tmp_path / config_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(current)
    outputs = iter(
        (
            f"{config_path}\0".encode(),
            b"",
            b"",
            b"",
            str(len(prior.encode())).encode(),
            prior.encode(),
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="frontend collection configuration",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_frontend_collection_configuration_dependency_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = "apps/control-center/vitest.config.ts"
    intermediate_path = "apps/control-center/vitest.shared.ts"
    dependency_path = "apps/control-center/vitest.discovery.ts"
    target = tmp_path / config_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        'import { shared } from "./vitest.shared";\nexport default shared;\n'
    )
    (tmp_path / intermediate_path).write_text(
        'export { shared } from "./vitest.discovery";\n'
    )
    (tmp_path / dependency_path).write_text("export const shared = {};\n")
    outputs = iter((f"{dependency_path}\0".encode(), b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="frontend collection configuration dependency",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_configured_vitest_setup_file_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = "apps/control-center/vite.config.ts"
    setup_path = "apps/control-center/src/test/setup.ts"
    target = tmp_path / config_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        'export default { test: { setupFiles: "./src/test/setup.ts" } };\n'
    )
    setup = tmp_path / setup_path
    setup.parent.mkdir(parents=True, exist_ok=True)
    setup.write_text("export {};\n")
    outputs = iter((f"{setup_path}\0".encode(), b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="frontend collection configuration dependency",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_frontend_test_script_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = "apps/control-center/package.json"
    current = '{"scripts":{"test":"vitest --exclude src/example.test.ts"}}\n'
    prior = '{"scripts":{"test":"vitest"}}\n'
    target = tmp_path / config_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(current)
    outputs = iter(
        (
            f"{config_path}\0".encode(),
            b"",
            b"",
            b"",
            str(len(prior.encode())).encode(),
            prior.encode(),
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    with pytest.raises(guard.TestCorpusGuardError, match="frontend test script"):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_frontend_pretest_script_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = "apps/control-center/package.json"
    current = '{"scripts":{"pretest":"node rewrite-config.js","test":"vitest"}}\n'
    prior = '{"scripts":{"pretest":"","test":"vitest"}}\n'
    target = tmp_path / config_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(current)
    outputs = iter(
        (
            f"{config_path}\0".encode(),
            b"",
            b"",
            b"",
            str(len(prior.encode())).encode(),
            prior.encode(),
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    with pytest.raises(guard.TestCorpusGuardError, match="frontend test script"):
        guard._changed_test_paths(tmp_path, "a" * 40)


@pytest.mark.parametrize(
    ("config_path", "current", "prior"),
    (
        (
            "apps/control-center/package.json",
            '{"scripts":{"test":"vitest"},"devDependencies":{"vitest":"4.1.8"}}\n',
            '{"scripts":{"test":"vitest"},"devDependencies":{"vitest":"4.1.7"}}\n',
        ),
        (
            "apps/control-center/package-lock.json",
            '{"lockfileVersion":3,"packages":{"node_modules/vitest":{"version":"4.1.8"}}}\n',
            '{"lockfileVersion":3,"packages":{"node_modules/vitest":{"version":"4.1.7"}}}\n',
        ),
        (
            "apps/control-center/npm-shrinkwrap.json",
            '{"lockfileVersion":3,"packages":{"node_modules/vitest":{"version":"4.1.8"}}}\n',
            '{"lockfileVersion":3,"packages":{"node_modules/vitest":{"version":"4.1.7"}}}\n',
        ),
    ),
)
def test_changed_frontend_test_dependency_boundary_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    config_path: str,
    current: str,
    prior: str,
) -> None:
    target = tmp_path / config_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(current)
    outputs = iter((f"{config_path}\0".encode(), b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: prior if path == config_path else None,
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="frontend test dependency boundary",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_frontend_test_dataset_rechecks_importing_test(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_root = tmp_path / "apps/control-center/src"
    source_root.mkdir(parents=True)
    (source_root / "cases.test.ts").write_text(
        'export const CASES = [["one"]] as const;\n'
    )
    (source_root / "consumer.test.ts").write_text(
        'import { CASES } from "./cases.test";\n'
        'test.each(CASES)("renders %s", () => {});\n'
    )
    outputs = iter(
        (
            b"apps/control-center/src/cases.test.ts\0",
            b"",
            b"",
            b"",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=next(outputs),
            stderr=b"",
        ),
    )

    assert guard._changed_test_paths(tmp_path, "a" * 40) == (
        "apps/control-center/src/cases.test.ts",
        "apps/control-center/src/consumer.test.ts",
    )


def test_python_inventory_rejects_package_relative_parameter_import(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="relative imported Python parameter data",
    ):
        guard._parse_worktree_test_declarations(
            tmp_path,
            "tests/test_sample.py",
            """
import pytest
from . import CASES

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value
""",
        )


def test_python_inventory_binds_transitive_imported_parameter_source(
    tmp_path: Path,
) -> None:
    scripts_root = tmp_path / "scripts"
    scripts_root.mkdir()
    (scripts_root / "data.py").write_text(
        "from scripts.helpers import build_cases\nCASES = build_cases()\n"
    )
    helper_path = scripts_root / "helpers.py"
    helper_path.write_text('def build_cases():\n    return ["one", "two"]\n')
    test_text = """
import pytest
from scripts.data import CASES

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value
"""

    before = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )
    helper_path.write_text('def build_cases():\n    return ["one"]\n')
    after = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )

    assert before[0].ref != after[0].ref


def test_python_inventory_hashes_only_exact_imported_parameter_binding(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "data.py"
    source_path.write_text('CASES = ["one"]\nUNRELATED = "before"\n')
    test_text = """
import pytest
from data import CASES

@pytest.mark.parametrize("value", list(CASES))
def test_case(value):
    assert value
"""
    before = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )
    source_path.write_text('CASES = ["one"]\nUNRELATED = "after"\n')
    unrelated = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )
    source_path.write_text('CASES = ["one", "two"]\nUNRELATED = "after"\n')
    changed = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )

    assert before[0].ref == unrelated[0].ref
    assert before[0].ref != changed[0].ref


def test_python_inventory_ignores_imported_parameter_callable_bodies(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "data.py"
    source_path.write_text(
        "class Case:\n"
        "    def value(self): return 'before'\n"
        "def validator(value): return value == 'before'\n"
    )
    test_text = """
import pytest
from data import Case, validator

@pytest.mark.parametrize(("case_type", "check"), [(Case, validator)])
def test_case(case_type, check):
    assert check(case_type().value())
"""
    before = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )
    source_path.write_text(
        "class Case:\n"
        "    def value(self): return 'after'\n"
        "def validator(value): return value == 'after'\n"
    )
    after = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )

    assert before[0].ref == after[0].ref


def test_python_inventory_binds_materialized_parameter_class_bodies(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "data.py"
    source_path.write_text(
        "class Case:\n"
        "    def __init__(self): self.value = 'before'\n"
    )
    test_text = """
import pytest
from data import Case

@pytest.mark.parametrize("case", [Case()])
def test_case(case):
    assert case.value
"""
    before = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )
    source_path.write_text(
        "class Case:\n"
        "    def __init__(self): self.value = 'after'\n"
    )
    after = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )

    assert before[0].ref != after[0].ref


def test_python_inventory_binds_materialized_parameter_class_dependencies(
    tmp_path: Path,
) -> None:
    factory_path = tmp_path / "factory.py"
    data_path = tmp_path / "data.py"
    factory_path.write_text("def make_value():\n    return 'before'\n")
    data_path.write_text(
        "from factory import make_value\n"
        "class Case:\n"
        "    def __init__(self): self.value = make_value()\n"
    )
    test_text = """
import pytest
from data import Case

@pytest.mark.parametrize("case", [Case()])
def test_case(case):
    assert case.value
"""
    before = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )
    factory_path.write_text("def make_value():\n    return 'after'\n")
    after = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )

    assert before[0].ref != after[0].ref


def test_python_inventory_binds_materialized_parameter_factory_alias(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "data.py"
    source_path.write_text("def make_cases():\n    return ['before']\n")
    test_text = """
import pytest
from data import make_cases

factory = make_cases

@pytest.mark.parametrize("case", factory())
def test_case(case):
    assert case
"""
    before = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )
    source_path.write_text("def make_cases():\n    return ['after']\n")
    after = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )

    assert before[0].ref != after[0].ref


def test_python_inventory_binds_positional_imported_parameter_id_helper(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "data.py"
    source_path.write_text('def make_id(value):\n    return f"before-{value}"\n')
    test_text = """
import pytest
from data import make_id

@pytest.mark.parametrize("value", ["one"], False, make_id)
def test_case(value):
    assert value
"""
    before = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )
    source_path.write_text('def make_id(value):\n    return f"after-{value}"\n')
    after = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )

    assert before[0].ref != after[0].ref


def test_python_inventory_propagates_ids_materialization_through_binding(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "data.py"
    source_path.write_text('def make_id(value):\n    return f"before-{value}"\n')
    test_text = """
import pytest
from data import make_id

IDS = make_id

@pytest.mark.parametrize("value", ["one"], ids=IDS)
def test_case(value):
    assert value
"""
    before = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )
    source_path.write_text('def make_id(value):\n    return f"after-{value}"\n')
    after = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )

    assert before[0].ref != after[0].ref


def test_python_inventory_preserves_inert_callable_abort_posture(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "data.py"
    source_path.write_text("def helper():\n    return True\n")
    test_text = """
import pytest
from data import helper

@pytest.mark.parametrize("callback", [helper])
def test_case(callback):
    assert callback()
"""
    before = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )
    source_path.write_text(
        "import pytest\n"
        "def helper():\n"
        "    pytest.skip('disabled')\n"
    )
    after = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )

    assert before[0].ref != after[0].ref


def test_python_inventory_preserves_transitive_inert_callable_abort_posture(
    tmp_path: Path,
) -> None:
    dependency_path = tmp_path / "dependency.py"
    callback_path = tmp_path / "callback.py"
    dependency_path.write_text("def prepare():\n    return True\n")
    callback_path.write_text(
        "from dependency import prepare\n"
        "def helper():\n"
        "    return prepare()\n"
    )
    test_text = """
import pytest
from callback import helper

@pytest.mark.parametrize("callback", [helper])
def test_case(callback):
    assert callback()
"""
    before = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )
    dependency_path.write_text(
        "import pytest\n"
        "def prepare():\n"
        "    pytest.xfail('disabled')\n"
    )
    after = guard._parse_worktree_test_declarations(
        tmp_path, "tests/test_sample.py", test_text
    )

    assert before[0].ref != after[0].ref


def test_worktree_import_resolution_requires_exact_path_case(tmp_path: Path) -> None:
    package = tmp_path / "tests"
    package.mkdir()
    (package / "coordinator.py").write_text("VALUE = True\n")

    assert guard._worktree_path_has_exact_case(
        tmp_path,
        "tests/coordinator.py",
    )
    assert not guard._worktree_path_has_exact_case(
        tmp_path,
        "tests/Coordinator.py",
    )


def test_python_inventory_matches_class_collection_edge_cases() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        """
import unittest

def constructor(self):
    pass

class TestPlainObject(object):
    def test_collected(self):
        pass

class TestDisabled:
    __test__ = False
    def test_hidden(self):
        pass

class DisabledBase:
    __test__ = False
    def test_inherited_hidden(self):
        pass

class TestInheritedDisabled(DisabledBase):
    pass

class TestAssignedConstructor:
    __init__ = constructor
    def test_not_collected(self):
        pass

class CustomCase(unittest.TestCase):
    __init__ = constructor
    def test_unittest_collected(self):
        pass
""",
    )

    assert [item.ref for item in declarations] == [
        "tests/test_sample.py::TestPlainObject::test_collected",
        "tests/test_sample.py::CustomCase::test_unittest_collected",
    ]


def test_python_inventory_binds_inherited_class_parametrization_at_collection() -> None:
    template = """
import pytest

CASES = ["one"]

@pytest.mark.parametrize("value", CASES)
class Base:
    def test_case(self, value):
        assert value

{mutation}

class TestChild(Base):
    pass
"""
    before = guard.parse_python_declarations(
        "tests/test_sample.py", template.format(mutation="")
    )
    after = guard.parse_python_declarations(
        "tests/test_sample.py", template.format(mutation='CASES.append("two")')
    )

    assert before[0].ref != after[0].ref


def test_python_inventory_binds_helper_argument_mutation() -> None:
    template = """
import pytest

CASES = ["one"]

def add_case(values):
    values.append("two")

{mutation}

@pytest.mark.parametrize("value", CASES)
def test_case(value):
    assert value
"""
    before = guard.parse_python_declarations(
        "tests/test_sample.py", template.format(mutation="")
    )
    after = guard.parse_python_declarations(
        "tests/test_sample.py", template.format(mutation="add_case(CASES)")
    )

    assert before[0].ref != after[0].ref


def test_python_inventory_omits_fixture_named_like_test_and_rejects_fixture_params() -> (
    None
):
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        """
import pytest

@pytest.fixture
def test_fixture():
    return "value"

def test_collected():
    pass
""",
    )
    assert [item.ref for item in declarations] == [
        "tests/test_sample.py::test_collected"
    ]

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="parameterized Python fixtures",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            """
import pytest

@pytest.fixture(params=["one", "two"])
def value(request):
    return request.param

def test_collected(value):
    assert value
            """,
        )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="parameterized Python fixtures",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            """
import pytest

class TestGroup:
    parameterized_fixture = pytest.fixture(params=["one", "two"])

    @parameterized_fixture
    def value(self, request):
        return request.param

    def test_collected(self, value):
        assert value
""",
        )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="parameterized Python fixtures",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            """
import pytest

parameterized_fixture = pytest.fixture(params=["one", "two"])

@parameterized_fixture
def value(request):
    return request.param

def test_collected(value):
    assert value
""",
        )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="parameterized Python fixtures",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            """
import pytest

class TestGroup:
    @pytest.fixture(params=["one", "two"])
    def value(self, request):
        return request.param

    def test_collected(self, value):
        assert value
""",
        )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="parameterized Python fixtures",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            """
from pytest import fixture as f

@f(params=["one", "two"])
def value(request):
    return request.param

def test_collected(value):
    assert value
""",
        )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="parameterized Python fixtures",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            """
import pytest

OPTIONS = {"params": ["one", "two"]}
parameterized_fixture = pytest.fixture(**OPTIONS)

@parameterized_fixture
def value(request):
    return request.param

def test_collected(value):
    assert value
""",
        )


@pytest.mark.parametrize(
    ("source", "message"),
    (
        (
            "class TestGroup:\n    test_alias = helper\n",
            "class test-name assignment",
        ),
        (
            "@decorate\nclass TestGroup:\n    def test_case(self): pass\n",
            "test class decorator",
        ),
        (
            "class TestGroup:\n    def test_case(self): pass\n"
            "class TestGroup:\n    def test_other(self): pass\n",
            "duplicate Python class bindings",
        ),
        (
            "def test_case(): pass\ndef test_case(): pass\n",
            "duplicate Python test bindings",
        ),
        (
            "class First:\n    def test_first(self): pass\n"
            "class Second:\n    def test_second(self): pass\n"
            "class TestGroup(First, Second):\n    pass\n",
            "multiple Python test class inheritance",
        ),
        (
            "def test_case(): pass\nif enabled:\n    test_case.__test__ = False\n",
            "__test__ mutation inside module control flow",
        ),
        (
            "__test__ = False\ndef test_case(): pass\n",
            "module-level Python __test__ binding",
        ),
        (
            "from helpers import test_shared\n",
            "imported Python tests",
        ),
        (
            "from helpers import TestShared\n",
            "imported Python tests",
        ),
    ),
)
def test_python_inventory_rejects_ambiguous_collection_constructs(
    source: str,
    message: str,
) -> None:
    with pytest.raises(guard.TestCorpusGuardError, match=message):
        guard.parse_python_declarations("tests/test_sample.py", source)


def test_python_inventory_rejects_locally_imported_test_class(
    tmp_path: Path,
) -> None:
    test_root = tmp_path / "tests"
    test_root.mkdir()
    (test_root / "helpers.py").write_text(
        "class TestShared:\n    def test_case(self): pass\n"
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="imported Python tests",
    ):
        guard._parse_worktree_test_declarations(
            tmp_path,
            "tests/test_consumer.py",
            "from tests.helpers import TestShared\n",
        )


@pytest.mark.parametrize(
    "source",
    (
        "import pytest\n"
        'pytest.skip("unavailable", allow_module_level=True)\n'
        "def test_case(): pass\n",
        "import pytest as p\n"
        'p.importorskip("optional_dependency")\n'
        "def test_case(): pass\n",
        "from pytest import importorskip as require_module\n"
        'require_module("optional_dependency")\n'
        "def test_case(): pass\n",
        "import pytest\n"
        "abort = pytest.importorskip\n"
        'abort("optional_dependency")\n'
        "def test_case(): pass\n",
        "import pytest\n"
        "skip_module = pytest.skip\n"
        'skip_module("unavailable", allow_module_level=True)\n'
        "def test_case(): pass\n",
        "import pytest\n"
        'raise pytest.skip.Exception("unavailable", allow_module_level=True)\n'
        "def test_case(): pass\n",
        "from pytest import skip\n"
        "abort = skip\n"
        'raise abort.Exception("unavailable", allow_module_level=True)\n'
        "def test_case(): pass\n",
        "import pytest\n"
        "Abort = pytest.skip.Exception\n"
        'raise Abort("unavailable", allow_module_level=True)\n'
        "def test_case(): pass\n",
        "import pytest\n"
        "raise pytest.skip.Exception.__call__('unavailable')\n"
        "def test_case(): pass\n",
        "import pytest\n"
        "raise pytest.xfail.Exception.__call__('unavailable')\n"
        "def test_case(): pass\n",
        "import pytest\n"
        'getattr(pytest, "skip")("unavailable", allow_module_level=True)\n'
        "def test_case(): pass\n",
        "import pytest as p\n"
        'getattr(p, "importorskip")("optional_dependency")\n'
        "def test_case(): pass\n",
        "import pytest\n"
        "from builtins import getattr as attr\n"
        'attr(pytest, "skip")("unavailable", allow_module_level=True)\n'
        "def test_case(): pass\n",
        "import pytest\n"
        'getattr(pytest, "skip", pytest.skip)('
        '"unavailable", allow_module_level=True)\n'
        "def test_case(): pass\n",
        "import pytest\n"
        'getattr(pytest, "importorskip", pytest.importorskip)('
        '"optional_dependency")\n'
        "def test_case(): pass\n",
    ),
)
def test_python_inventory_rejects_module_collection_aborts(source: str) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="module-level pytest collection abort",
    ):
        guard.parse_python_declarations("tests/test_sample.py", source)


@pytest.mark.parametrize(
    "source",
    (
        "def setup_module(module): pass\ndef test_case(): pass\n",
        "def setup_function(function): pass\ndef test_case(): pass\n",
        "class TestCases:\n"
        "    @classmethod\n"
        "    def setup_class(cls): pass\n"
        "    def test_case(self): pass\n",
        "class TestCases:\n"
        "    def setup_method(self, method): pass\n"
        "    def test_case(self): pass\n",
        "def prepare(function): pass\n"
        "setup_function = prepare\n"
        "def test_case(): pass\n",
        "from tests.helper import prepare as setup_function\ndef test_case(): pass\n",
        "class TestCases:\n"
        "    def prepare(self, method): pass\n"
        "    setup_method = prepare\n"
        "    def test_case(self): pass\n",
        "def setUpModule(): pass\ndef test_case(): pass\n",
        "def prepare(module): pass\n"
        "setUpModule = prepare\n"
        "def test_case(): pass\n",
        "from tests.helper import prepare as setUpModule\n"
        "def test_case(): pass\n",
    ),
)
def test_python_inventory_rejects_xunit_setup_hooks(source: str) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="xunit-style pytest setup hooks",
    ):
        guard.parse_python_declarations("tests/test_sample.py", source)


@pytest.mark.parametrize(
    "source",
    (
        "import unittest\nraise unittest.SkipTest('unavailable')\n",
        "import unittest as unit\nraise unit.SkipTest('unavailable')\n",
        "from unittest import SkipTest as unavailable\nraise unavailable('missing')\n",
        "import unittest\nabort = unittest.SkipTest\nraise abort('missing')\n",
    ),
)
def test_python_inventory_rejects_unittest_module_collection_aborts(
    source: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="module-level unittest collection abort",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py", source + "def test_case(): pass\n"
        )


@pytest.mark.parametrize(
    "source",
    (
        'exec("def test_case(): pass")\n',
        'eval("lambda: None")\n',
        'runner = exec\nrunner("def test_case(): pass")\n',
        'import builtins as runtime\nruntime.exec("def test_case(): pass")\n',
        'from builtins import exec as runner\nrunner("def test_case(): pass")\n',
    ),
)
def test_python_inventory_rejects_module_dynamic_code(source: str) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="module-level dynamic Python code",
    ):
        guard.parse_python_declarations("tests/test_sample.py", source)


@pytest.mark.parametrize(
    "source",
    (
        "import pytest\npytest.Module.collect = lambda self: []\n"
        "def test_case(): pass\n",
        "from _pytest.python import Module\n"
        'setattr(Module, "collect", lambda self: [])\n'
        "def test_case(): pass\n",
    ),
)
def test_python_inventory_rejects_pytest_collection_class_mutation(
    source: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="pytest collection class mutation",
    ):
        guard.parse_python_declarations("tests/test_sample.py", source)


@pytest.mark.parametrize(
    "source",
    (
        'import pytest\ntype.__setattr__(pytest.Module, "collect", lambda self: [])\n'
        "def test_case(): pass\n",
        "from _pytest.python import Module\n"
        "mutate = type.__setattr__\n"
        'mutate(Module, "collect", lambda self: [])\n'
        "def test_case(): pass\n",
    ),
)
def test_python_inventory_rejects_descriptor_pytest_collection_class_mutation(
    source: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="pytest collection class mutation",
    ):
        guard.parse_python_declarations("tests/test_sample.py", source)


@pytest.mark.parametrize(
    "before,after",
    (
        (
            "import pytest\ndef test_case(): pass\n",
            "import pytest\n@pytest.mark.skip\ndef test_case(): pass\n",
        ),
        (
            "import pytest\ndef test_case(): pass\n",
            "import pytest\n@pytest.mark.skipif(True, reason='disabled')\n"
            "def test_case(): pass\n",
        ),
        (
            "import pytest\ndef test_case(): pass\n",
            "import pytest\npytestmark = pytest.mark.skipif(True, reason='disabled')\n"
            "def test_case(): pass\n",
        ),
        (
            "import pytest\ndef test_case(): pass\n",
            "import pytest\n@pytest.mark.xfail(run=False, reason='disabled')\n"
            "def test_case(): pass\n",
        ),
        (
            "import pytest\ndef test_case(): pass\n",
            "import pytest\n@pytest.mark.xfail(reason='expected')\n"
            "def test_case(): assert False\n",
        ),
        (
            "import pytest\ndef test_case(): pass\n",
            "import pytest\npytestmark = pytest.mark.xfail("
            "run=False, reason='disabled')\ndef test_case(): pass\n",
        ),
    ),
)
def test_python_inventory_binds_execution_disabling_marks(
    before: str,
    after: str,
) -> None:
    before_ref = guard.parse_python_declarations("tests/test_sample.py", before)[0].ref
    after_ref = guard.parse_python_declarations("tests/test_sample.py", after)[0].ref

    assert before_ref != after_ref


def test_python_inventory_rejects_dynamic_xfail_run_condition() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="xfail run condition",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "import pytest\n"
            "@pytest.mark.xfail(run=feature_enabled, reason='conditional')\n"
            "def test_case(): pass\n",
        )


def test_python_inventory_binds_referenced_xfail_condition() -> None:
    before = (
        "import pytest\nDISABLED = False\n"
        "@pytest.mark.xfail(DISABLED, run=False)\n"
        "def test_case(): pass\n"
    )
    after = before.replace("DISABLED = False", "DISABLED = True")

    before_ref = guard.parse_python_declarations("tests/test_sample.py", before)[0].ref
    after_ref = guard.parse_python_declarations("tests/test_sample.py", after)[0].ref

    assert before_ref != after_ref


def test_python_inventory_binds_imported_xfail_condition(tmp_path: Path) -> None:
    test_path = "tests/test_sample.py"
    flags_path = tmp_path / "tests/xfail_flags.py"
    flags_path.parent.mkdir(parents=True)
    flags_path.write_text("DISABLED = False\n")
    test_text = (
        "import pytest\nfrom tests.xfail_flags import DISABLED\n"
        "@pytest.mark.xfail(DISABLED, run=False)\n"
        "def test_case(): pass\n"
    )

    before_ref = guard._parse_worktree_test_declarations(
        tmp_path, test_path, test_text
    )[0].ref
    flags_path.write_text("DISABLED = True\n")
    after_ref = guard._parse_worktree_test_declarations(tmp_path, test_path, test_text)[
        0
    ].ref

    assert before_ref != after_ref


def test_python_inventory_preserves_competing_xfail_order() -> None:
    first = (
        "import pytest\n"
        "@pytest.mark.xfail(True, run=False)\n"
        "@pytest.mark.xfail(True, run=True)\n"
        "def test_case(): pass\n"
    )
    second = first.replace(
        "@pytest.mark.xfail(True, run=False)\n@pytest.mark.xfail(True, run=True)",
        "@pytest.mark.xfail(True, run=True)\n@pytest.mark.xfail(True, run=False)",
    )

    first_ref = guard.parse_python_declarations("tests/test_sample.py", first)[0].ref
    second_ref = guard.parse_python_declarations("tests/test_sample.py", second)[0].ref

    assert first_ref != second_ref


@pytest.mark.parametrize(
    "mutation",
    (
        "sys.modules[__name__].test_case = None",
        'sys.modules[__name__].__dict__["test_case"] = None',
        'sys.modules[__name__].__dict__.pop("test_case")',
        'vars(sys.modules[__name__]).update({"test_case": None})',
        'setattr(sys.modules[__name__], "test_case", None)',
        'sys.modules.get(__name__).__dict__.pop("test_case")',
        'sys.modules.get(__name__, None).__dict__.pop("test_case")',
    ),
)
def test_python_inventory_rejects_current_module_test_rebinding(
    mutation: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="indirect Python test-name rebinding",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            f"import sys\ndef test_case(): pass\n{mutation}\n",
        )


def test_python_inventory_allows_noncallable_test_like_bindings() -> None:
    declarations = guard.parse_python_declarations(
        "tests/test_sample.py",
        "test_data = [1, 2]\n"
        'TestSettings = {"mode": "safe"}\n'
        "test_label = 'safe'\n"
        "test_timeout_ms = 30 * 1000\n"
        "def test_case(): pass\n",
    )

    assert [declaration.ref for declaration in declarations] == [
        "tests/test_sample.py::test_case"
    ]


def test_frontend_inventory_preserves_unchanged_static_registration_loop_items() -> (
    None
):
    before = """
const cases = [{ name: "one" }, { name: "two" }] as const;
for (const item of cases) {
  test(`${item.name} works`, () => {});
}
"""
    after = before.replace(', { name: "two" }', ', { name: "three" }')
    path = "apps/control-center/src/example.test.ts"
    before_refs = {item.ref for item in guard.parse_frontend_declarations(path, before)}
    after_refs = {item.ref for item in guard.parse_frontend_declarations(path, after)}

    assert len(before_refs) == len(after_refs) == 2
    assert len(before_refs & after_refs) == 1
    assert len(before_refs - after_refs) == 1
    assert len(after_refs - before_refs) == 1


def test_frontend_registration_loop_identity_ignores_unused_item_fields() -> None:
    before = """
const cases = [{ name: "one", enabled: true }] as const;
for (const item of cases) {
  test(`${item.name} works`, () => {});
}
"""
    after = before.replace("enabled: true", "enabled: false")
    path = "apps/control-center/src/example.test.ts"
    before_declarations = guard.parse_frontend_declarations(path, before)
    after_declarations = guard.parse_frontend_declarations(path, after)

    assert [item.ref for item in before_declarations] == [f"{path}::one works"]
    assert [item.ref for item in after_declarations] == [f"{path}::one works"]
    assert guard._source_ref_from_text(before_declarations[0].ref, before) != (
        guard._source_ref_from_text(after_declarations[0].ref, after)
    )


def test_frontend_registration_loop_preserves_runtime_title_whitespace() -> None:
    path = "apps/control-center/src/example.test.ts"
    compact = 'const cases = ["a b"] as const;\nfor (const item of cases) { test(`${item}`, () => {}); }\n'
    spaced = compact.replace('"a b"', '" a  b "')

    assert guard.parse_frontend_declarations(path, compact)[0].ref == f"{path}::a b"
    assert guard.parse_frontend_declarations(path, spaced)[0].ref == f"{path}:: a  b "


def test_frontend_inventory_binds_enclosing_suite_titles() -> None:
    path = "apps/control-center/src/example.test.ts"
    before = 'describe("one", () => { test("case", () => {}); });\n'
    after = before.replace('"one"', '"two"')

    before_ref = guard.parse_frontend_declarations(path, before)[0].ref
    after_ref = guard.parse_frontend_declarations(path, after)[0].ref

    assert before_ref == f"{path}::suite[3]:one::case"
    assert after_ref == f"{path}::suite[3]:two::case"


def test_frontend_inventory_binds_enclosing_suite_execution_posture() -> None:
    path = "apps/control-center/src/example.test.ts"
    active = 'describe("suite", () => { test("case", () => {}); });\n'
    disabled = active.replace("describe(", "describe.skip(")

    active_ref = guard.parse_frontend_declarations(path, active)[0].ref
    disabled_ref = guard.parse_frontend_declarations(path, disabled)[0].ref

    assert active_ref != disabled_ref
    assert "::execution-disabled:skip::identity-sha256:" in disabled_ref


def test_frontend_registration_loop_combines_unicode_surrogate_pairs() -> None:
    path = "apps/control-center/src/example.test.ts"
    escaped = r'const cases = ["\uD83D\uDE00"] as const;' + "\n"
    escaped += "for (const item of cases) { test(`${item}`, () => {}); }\n"
    literal = escaped.replace(r'"\uD83D\uDE00"', '"😀"')

    assert guard.parse_frontend_declarations(path, escaped)[0].ref == (
        guard.parse_frontend_declarations(path, literal)[0].ref
    )


def test_frontend_registration_loop_accepts_comments_in_static_items() -> None:
    source = """
const cases = [/* first */ { name: "one", /* retained */ enabled: true }] as const;
for (const item of cases) { test(`${item.name}`, () => {}); }
"""

    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.ts", source
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.test.ts::one"
    ]


@pytest.mark.parametrize(
    ("source", "message"),
    (
        (
            'const cases = ["one", , "three"] as const;\n'
            "for (const item of cases) { test(`${item}`, () => {}); }",
            "sparse",
        ),
        (
            "const cases = [1.0] as const;\n"
            "for (const item of cases) { test(`${item}`, () => {}); }",
            "numeric titles",
        ),
        (
            'const cases = [{ name: "one" }] as const;\n'
            "for await (const item of cases) { test(`${item.name}`, () => {}); }",
            "registration context",
        ),
        (
            'const base = [{ name: "one" }] as const;\n'
            "const cases = base;\n"
            'cases[0].name = "two";\n'
            "for (const item of cases) { test(`${item.name}`, () => {}); }",
            "mutated before collection",
        ),
        (
            'import { test as spec } from "vitest";\n'
            '{ const spec = () => {}; spec("fake", () => {}); }',
            "shadowed",
        ),
        (
            'function register({ nested = {} } = {}) { test("case", () => {}); }',
            "registration context",
        ),
        (
            "const cases = [{ active: true }] as const;\n"
            'for (const item of cases) { if (item.active) test("case", () => {}); }',
            "registration context",
        ),
        (
            'if (enabled) /* controlled */ test("case", () => {});',
            "registration context",
        ),
        (
            'if (enabled) // controlled\n test("case", () => {});',
            "registration context",
        ),
        (
            'if (enabled) void 0, test("case", () => {});',
            "registration context",
        ),
        (
            'for await (const item of cases) /* controlled */ test("case", () => {});',
            "registration context",
        ),
        (
            'function inner() { return [["one"]]; }\n'
            "function build() { return inner(); }\n"
            "const cases = [...build()] as const;\n"
            'test.each(cases)("case %s", () => {});',
            "transitive helper",
        ),
        (
            'function buildCases() { return [["one"]]; }\n'
            'test.each(buildCases())("case %s", () => {});',
            "cannot be resolved safely",
        ),
    ),
)
def test_frontend_inventory_rejects_additional_unproven_collection_shapes(
    source: str,
    message: str,
) -> None:
    with pytest.raises(guard.TestCorpusGuardError, match=message):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts", source
        )


@pytest.mark.parametrize(
    ("source", "message"),
    (
        (
            'const cases = [["one"]]\n.slice();\n'
            'test.each(cases)("case %s", () => {});\n',
            "ASI continuation",
        ),
        (
            'import * as runner from "vitest";\n'
            "const { test: localTest } = runner;\n"
            'localTest("case", () => {});\n',
            "namespace-derived test API",
        ),
        (
            'function register() { test("case", () => {}); }\nregister();\n',
            "registration context",
        ),
        (
            'function register(): void { test("case", () => {}); }\nregister();\n',
            "registration context",
        ),
        (
            "function register(): keyof { a: string } { "
            'test("case", () => {}); return "a"; }\nregister();\n',
            "registration context",
        ),
        (
            "function register(value: unknown): value is { a: string } { "
            'test("case", () => {}); return true; }\nregister();\n',
            "registration context",
        ),
        (
            'const helper = { register() { test("case", () => {}); } };\n',
            "registration context",
        ),
        (
            'class Helper { register() { test("case", () => {}); } }\n',
            "registration context",
        ),
        (
            'class Registrar { registration = test("case", () => {}); }\n',
            "registration context",
        ),
        (
            "class Registrar extends Generic<{ field: string }> { "
            'registration = test("case", () => {}); }\n',
            "registration context",
        ),
        (
            'class Registrar { ["registration"] = test("case", () => {}); }\n',
            "registration context",
        ),
        (
            'class Registrar { method() {} registration = test("case", () => {}); }\n',
            "registration context",
        ),
        (
            'describe("suite", () => { if (!enabled) return; '
            'test("case", () => {}); });\n',
            "registration context",
        ),
        (
            'describe("suite", () => { if (!enabled) { throw new Error(); } '
            'test("case", () => {}); });\n',
            "registration context",
        ),
        (
            'describe("suite", () => { switch (mode) { case "off": return; } '
            'test("case", () => {}); });\n',
            "registration context",
        ),
        (
            'describe("suite", () => { return; '
            'test("case", () => {}); });\n',
            "registration context",
        ),
        (
            'describe("suite", () => {\n  return\n  '
            'test("case", () => {});\n});\n',
            "registration context",
        ),
        (
            'describe("suite", () => { return\u2028'
            'test("case", () => {}); });\n',
            "registration context",
        ),
        (
            'describe("suite", () => { return\u2029'
            'test("case", () => {}); });\n',
            "registration context",
        ),
        (
            'describe("suite", () => { throw new Error(); '
            'test("case", () => {}); });\n',
            "registration context",
        ),
        (
            'class Helper { register<T>() { test("case", () => {}); } }\n',
            "registration context",
        ),
        (
            "class Helper { "
            'register<T extends { id: string }>() { test("case", () => {}); } '
            "}\n",
            "registration context",
        ),
        (
            'const register = () => test("case", () => {});\n',
            "registration context",
        ),
        (
            'consume(() => { test("case", () => {}); });\n',
            "registration context",
        ),
        (
            'for (let index = 0; index < 2; index += 1) { test("case", () => {}); }',
            "registration loop",
        ),
        (
            'enabled && test("case", () => {});',
            "conditional test registration",
        ),
        (
            'enabled ? test("case", () => {}) : undefined;',
            "conditional test registration",
        ),
        (
            'const enabled = true; enabled && ({}, test("case", () => {}));',
            "conditional test registration",
        ),
        (
            'enabled && (() => {}, test("case", () => {}));',
            "conditional test registration",
        ),
    ),
)
def test_frontend_inventory_rejects_unproven_registration_constructs(
    source: str,
    message: str,
) -> None:
    with pytest.raises(guard.TestCorpusGuardError, match=message):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            source,
        )


def test_frontend_inventory_allows_callback_ternary_before_registration() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.ts",
        """
describe("suite", () => {
  const expected = enabled ? "one" : "two";
  test("case", () => expect(expected).toBe("one"));
});
describe("function suite", function () {
  const expected = enabled ? "one" : "two";
  test("function case", () => expect(expected).toBe("one"));
});
""",
    )

    assert len(declarations) == 2
    assert declarations[0].ref.endswith("::case")
    assert declarations[1].ref.endswith("::function case")


def test_frontend_inventory_allows_static_field_registration() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.ts",
        'class Registrar { static registration = test("case", () => {}); }\n',
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.test.ts::case"
    ]


@pytest.mark.parametrize(
    "source",
    (
        'import "./registerCases";\n',
        'import /* collection registration */ "./registerCases";\n',
        'import // collection registration\n "./registerCases";\n',
        'import {} from "./registerCases";\n',
    ),
)
def test_frontend_inventory_rejects_relative_side_effect_imports(source: str) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="side-effect import",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            source,
        )


def test_frontend_inventory_rejects_imported_registration_helper_call() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="imported frontend registration helper",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            'import { registerCases } from "./registerCases";\nregisterCases();\n',
        )


@pytest.mark.parametrize(
    "source",
    (
        'test.call(null, "case", () => {});\n',
        'test.apply(null, ["case", () => {}]);\n',
        'test.bind(null)("case", () => {});\n',
        'globalThis.test("case", () => {});\n',
        'globalThis.test?.("case", () => {});\n',
        'globalThis?.test?.("case", () => {});\n',
        'globalThis?.test.each([[1], [2]])("case %s", () => {});\n',
        'globalThis?.test["each"]([[1], [2]])("case %s", () => {});\n',
        'globalThis?.test["skip"]["each"]([[1]])("case %s", () => {});\n',
        'globalThis?.["test"]?.["skip"]?.["each"]([[1]])("case %s", () => {});\n',
        'globalThis["test"]("case", () => {});\n',
        'globalThis["test"]?.("case", () => {});\n',
        'globalThis?.["test"]("case", () => {});\n',
        '(0, test)("case", () => {});\n',
    ),
)
def test_frontend_inventory_rejects_indirect_runner_invocations(source: str) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="indirect frontend test registration",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            source,
        )


@pytest.mark.parametrize(
    "source",
    (
        '(test)("case", () => {});\n',
        '(enabled ? test : fallback)("case", () => {});\n',
        '(enabled && test)("case", () => {});\n',
    ),
)
def test_frontend_inventory_rejects_parenthesized_runner_callees(source: str) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="indirect frontend test registration",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            source,
        )


def test_frontend_inventory_rejects_dynamic_runner_import_binding() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic frontend runner import",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            'const { test: spec } = await import("vitest");\nspec("case", () => {});\n',
        )


def test_frontend_inventory_allows_type_only_runner_import_expression() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.ts",
        'function helper(page: import("@playwright/test").Page) { return page; }\n'
        'test("case", () => {});\n',
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.test.ts::case"
    ]


def test_frontend_inventory_allows_type_query_runner_import_expression() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.ts",
        'type Runner = typeof import("vitest");\ntest("case", () => {});\n',
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.test.ts::case"
    ]


def test_frontend_inventory_allows_generic_type_query_runner_import_expression() -> (
    None
):
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.ts",
        'type Runner<T extends typeof import("vitest")> = T;\n'
        'test("case", () => {});\n',
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.test.ts::case"
    ]


def test_frontend_inventory_rejects_glob_registration_import() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="frontend glob registration import",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            'const modules = import.meta.glob("./*.test.ts", { eager: true });\n'
            'test("case", () => modules);\n',
        )


@pytest.mark.parametrize(
    "source",
    (
        'const runner = enabled ? fallback : import("vitest");\n',
        'const runner = { load: import("vitest") };\n',
        'const runner = typeof import("vitest");\n',
    ),
)
def test_frontend_inventory_rejects_runtime_runner_import_contexts(source: str) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic frontend runner import",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            source + 'test("case", () => {});\n',
        )


def test_frontend_inventory_preserves_commented_runner_aliases() -> None:
    declarations = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.ts",
        "import { test /* test alias */ as spec, describe /* suite alias */ as group } "
        'from "vitest";\n'
        'group("suite", () => { spec("case", () => {}); });\n',
    )

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.test.ts::suite[5]:suite::case"
    ]


def test_frontend_inventory_binds_nested_spread_parameter_data() -> None:
    path = "apps/control-center/src/example.test.ts"
    before = """
const cases = [["one"]] as const;
test.each([...cases])("case %s", () => {});
"""
    after = before.replace('[["one"]]', '[["one"], ["two"]]')

    assert guard.parse_frontend_declarations(path, before)[0].ref != (
        guard.parse_frontend_declarations(path, after)[0].ref
    )


def test_frontend_inventory_binds_nested_imported_parameter_data(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "apps/control-center/src"
    source_root.mkdir(parents=True)
    source_path = source_root / "cases.ts"
    source_path.write_text('export const CASES = [["one"]] as const;\n')
    test_text = """
import { CASES } from "./cases";
test.each([...CASES])("case %s", () => {});
"""
    before = guard._parse_worktree_test_declarations(
        tmp_path,
        "apps/control-center/src/example.test.ts",
        test_text,
    )
    source_path.write_text('export const CASES = [["one"], ["two"]] as const;\n')
    after = guard._parse_worktree_test_declarations(
        tmp_path,
        "apps/control-center/src/example.test.ts",
        test_text,
    )

    assert before[0].ref != after[0].ref


@pytest.mark.parametrize(
    "hook_source",
    (
        "def pytest_collection_modifyitems(items):\n    items.clear()\n",
        "def pytest_generate_tests(metafunc):\n    metafunc.parametrize('value', [1])\n",
        "def pytest_pycollect_makeitem(collector, name, obj):\n    return []\n",
        "def pytest_collect_directory(path, parent):\n    return None\n",
        "def pytest_configure(config):\n"
        "    config.getini('python_functions').clear()\n",
        "def pytest_sessionstart(session):\n"
        "    session.config.getini('python_functions').clear()\n",
        "def pytest_sessionfinish(session):\n    session.exitstatus = 0\n",
    ),
)
def test_changed_conftest_collection_hook_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    hook_source: str,
) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/conftest.py").write_text(hook_source)
    outputs = iter((b"tests/conftest.py\0", b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(guard, "_base_text", lambda _repo, _base, _path: None)

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed pytest collection hooks",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


@pytest.mark.parametrize(
    "mutation_source",
    (
        "import tests.test_target as target\n"
        "target.test_case.__test__ = False\n",
        "from tests.test_target import test_case\n"
        "setattr(test_case, '__test__', False)\n",
        "from tests import test_target as target\n"
        "alias = target.test_case\n"
        "del alias.__test__\n",
        "import tests.test_target as target\n"
        "object.__setattr__(target.test_case, '__test__', False)\n",
        "import tests.test_target as target\n"
        "def disable():\n"
        "    target.test_case.__test__ = False\n"
        "disable()\n",
        "import tests.test_target as target\n"
        "target.test_case.__dict__['__' + 'test__'] = False\n",
    ),
)
def test_changed_conftest_imported_test_mutation_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation_source: str,
) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/conftest.py").write_text(mutation_source)
    outputs = iter((b"tests/conftest.py\0", b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(guard, "_base_text", lambda _repo, _base, _path: None)

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed conftest test declaration mutation",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_conftest_computed_hookimpl_spec_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/conftest.py").write_text(
        "import pytest\n"
        '@pytest.hookimpl(specname="pytest_" + "collection_modifyitems")\n'
        "def customize(items):\n"
        "    items.clear()\n"
    )
    outputs = iter((b"tests/conftest.py\0", b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(guard, "_base_text", lambda _repo, _base, _path: None)

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed pytest collection hooks",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_conftest_computed_collection_global_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/conftest.py").write_text(
        'globals()["collect_" + "ignore"] = ["test_target.py"]\n'
    )
    outputs = iter((b"tests/conftest.py\0", b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(guard, "_base_text", lambda _repo, _base, _path: None)

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="pytest plugin registration cannot be inventoried safely",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_conftest_pytest_plugins_binding_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "conftest.py").write_text(
        'pytest_plugins = ["tests.collection_plugin"]\n'
    )
    (tests_root / "collection_plugin.py").write_text(
        "def pytest_collection_modifyitems(items):\n    items.clear()\n"
    )
    outputs = iter((b"tests/conftest.py\0", b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "pytest_plugins = []\n" if path == "tests/conftest.py" else None
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed pytest plugin registration",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


@pytest.mark.parametrize(
    "source",
    (
        'globals()["pytest_plugins"] = ["tests.collection_plugin"]\n',
        'locals()["pytest_plugins"] = ["tests.collection_plugin"]\n',
        'vars()["pytest_plugins"] = ["tests.collection_plugin"]\n',
        "namespace = globals()\n"
        'namespace["pytest_plugins"] = ["tests.collection_plugin"]\n',
        "namespace = locals()\n"
        'namespace["pytest_plugins"] = ["tests.collection_plugin"]\n',
        "namespace = vars()\n"
        'namespace["pytest_plugins"] = ["tests.collection_plugin"]\n',
    ),
)
def test_indirect_pytest_plugins_binding_fails_closed(source: str) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="pytest plugin registration",
    ):
        guard._pytest_plugin_modules(source, "tests/conftest.py")


def test_conditional_test_module_pytest_plugin_registration_fails_closed() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="conditional pytest plugin registration",
    ):
        guard._pytest_plugin_modules(
            'if True:\n    pytest_plugins = ("tests.fixture_plugin",)\n',
            "tests/test_case.py",
        )


def test_changed_conftest_parameterized_fixture_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/conftest.py").write_text(
        "import pytest\n"
        '@pytest.fixture(params=["one"])\n'
        "def shared_value(request): return request.param\n"
    )
    outputs = iter((b"tests/conftest.py\0", b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(guard, "_base_text", lambda _repo, _base, _path: None)

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed parameterized pytest fixtures",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_conftest_autouse_fixture_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/conftest.py").write_text(
        "import pytest\n"
        "@pytest.fixture(autouse=True)\n"
        'def disable_subtree(): pytest.skip("disabled")\n'
    )
    outputs = iter((b"tests/conftest.py\0", b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(guard, "_base_text", lambda _repo, _base, _path: None)

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="Python fixtures",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_conftest_ordinary_fixture_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/conftest.py").write_text(
        "import pytest\n@pytest.fixture\ndef shared_value(): return 'current'\n"
    )
    outputs = iter((b"tests/conftest.py\0", b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "import pytest\n@pytest.fixture\ndef shared_value(): return 'prior'\n"
            if path == "tests/conftest.py"
            else None
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed pytest fixtures",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


@pytest.mark.parametrize(
    "fixture_prefix",
    (
        "@pytest.fixture(autouse=True)\n",
        "fixture_alias = pytest.fixture\n@fixture_alias(autouse=True)\n",
        "autouse_fixture = pytest.fixture(autouse=True)\n@autouse_fixture\n",
    ),
)
def test_python_inventory_binds_autouse_fixture_source(fixture_prefix: str) -> None:
    active = guard.parse_python_declarations(
        "tests/test_example.py",
        "import pytest\n"
        f"{fixture_prefix}"
        "def environment(): yield\n"
        "def test_case(): pass\n",
    )
    disabled = guard.parse_python_declarations(
        "tests/test_example.py",
        "import pytest\n"
        f"{fixture_prefix}"
        'def environment(): pytest.skip("disabled")\n'
        "def test_case(): pass\n",
    )

    assert {declaration.ref for declaration in active} != {
        declaration.ref for declaration in disabled
    }


def test_python_inventory_binds_autouse_fixture_helper_source() -> None:
    active = guard.parse_python_declarations(
        "tests/test_example.py",
        "import pytest\n"
        "def setup_environment(): return None\n"
        "@pytest.fixture(autouse=True)\n"
        "def environment(): setup_environment()\n"
        "def test_case(): pass\n",
    )
    disabled = guard.parse_python_declarations(
        "tests/test_example.py",
        "import pytest\n"
        "def setup_environment(): pytest.skip('disabled')\n"
        "@pytest.fixture(autouse=True)\n"
        "def environment(): setup_environment()\n"
        "def test_case(): pass\n",
    )

    assert {declaration.ref for declaration in active} != {
        declaration.ref for declaration in disabled
    }


def test_python_inventory_binds_imported_autouse_fixture_helper_source() -> None:
    test_source = (
        "import pytest\n"
        "from tests.helper import setup_environment\n"
        "@pytest.fixture(autouse=True)\n"
        "def environment(): setup_environment()\n"
        "def test_case(): pass\n"
    )

    def refs_for(posture: str) -> tuple[str, ...]:
        resolver = guard._python_import_resolver(
            lambda path: (
                f"def setup_environment(): {posture}\n"
                if path == "tests/helper.py"
                else None
            )
        )
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_example.py",
                test_source,
                resolver,
            )
        )

    assert refs_for("return None") != refs_for("raise RuntimeError('disabled')")


@pytest.mark.parametrize(
    "import_statement",
    (
        "from tests import helper as helper_module",
        "import tests.helper as helper_module",
    ),
)
def test_python_inventory_binds_autouse_fixture_imported_module_alias(
    import_statement: str,
) -> None:
    test_source = (
        "import pytest\n"
        f"{import_statement}\n"
        "@pytest.fixture(autouse=True)\n"
        "def environment(monkeypatch):\n"
        "    monkeypatch.setattr(helper_module, 'enabled', False)\n"
        "def test_case(): pass\n"
    )

    def refs_for(enabled: bool) -> tuple[str, ...]:
        resolver = guard._python_import_resolver(
            lambda path: (
                f"enabled = {enabled!r}\n" if path == "tests/helper.py" else None
            )
        )
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_example.py",
                test_source,
                resolver,
            )
        )

    assert refs_for(True) != refs_for(False)


def test_python_inventory_binds_autouse_fixture_module_dependency_closure() -> None:
    test_source = (
        "import pytest\n"
        "import tests.helper as helper_module\n"
        "def run_setup(module): module.setup_environment()\n"
        "@pytest.fixture(autouse=True)\n"
        "def environment(): run_setup(helper_module)\n"
        "def test_case(): pass\n"
    )

    def refs_for(enabled: bool) -> tuple[str, ...]:
        resolver = guard._python_import_resolver(
            lambda path: (
                "from tests.state import enabled\n"
                "def setup_environment(): return enabled\n"
                if path == "tests/helper.py"
                else f"enabled = {enabled!r}\n"
                if path == "tests/state.py"
                else None
            )
        )
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_example.py",
                test_source,
                resolver,
            )
        )

    assert refs_for(True) != refs_for(False)


@pytest.mark.parametrize(
    "fixture_declaration",
    (
        "@pytest.fixture\ndef value(): return fixture_value()\n",
        "@pytest.fixture(name='value')\ndef _value(): return fixture_value()\n",
        "def value(): return fixture_value()\nvalue = pytest.fixture(value)\n",
    ),
)
def test_python_inventory_binds_module_local_requested_fixture(
    fixture_declaration: str,
) -> None:
    def refs_for(enabled: bool) -> tuple[str, ...]:
        source = (
            "import pytest\n"
            f"def fixture_value(): return {enabled!r}\n"
            + fixture_declaration
            + "def test_case(value): pass\n"
        )
        return tuple(
            declaration.ref
            for declaration in guard.parse_python_declarations(
                "tests/test_example.py",
                source,
            )
        )

    assert refs_for(True) != refs_for(False)


def test_python_inventory_binds_usefixtures_local_fixture() -> None:
    def refs_for(enabled: bool) -> tuple[str, ...]:
        return tuple(
            declaration.ref
            for declaration in guard.parse_python_declarations(
                "tests/test_example.py",
                "import pytest\n"
                "@pytest.fixture\n"
                f"def value(): return {enabled!r}\n"
                '@pytest.mark.usefixtures("value")\n'
                "def test_case(): pass\n",
            )
        )

    assert refs_for(True) != refs_for(False)


def test_python_inventory_binds_local_fixture_dependencies() -> None:
    def refs_for(enabled: bool) -> tuple[str, ...]:
        return tuple(
            declaration.ref
            for declaration in guard.parse_python_declarations(
                "tests/test_example.py",
                "import pytest\n"
                "@pytest.fixture\n"
                f"def base(): return {enabled!r}\n"
                "@pytest.fixture\n"
                "def value(base): return base\n"
                "def test_case(value): pass\n",
            )
        )

    assert refs_for(True) != refs_for(False)


@pytest.mark.parametrize(
    "bindings",
    (
        "from tests.helper import value\n"
        "@pytest.fixture\n"
        "def value(): return 'local'\n",
        "@pytest.fixture\n"
        "def value(): return 'local'\n"
        "from tests.helper import value\n",
    ),
)
def test_python_inventory_rejects_local_fixture_import_name_collision(
    bindings: str,
) -> None:
    resolver = guard._python_import_resolver(
        lambda path: (
            "def value(): return 'imported'\n" if path == "tests/helper.py" else None
        )
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="imported Python fixture name is ambiguous",
    ):
        guard._python_inventory_entries(
            "tests/test_example.py",
            "import pytest\n" + bindings + "def test_case(value): pass\n",
            resolver,
        )


@pytest.mark.parametrize(
    "reassignment",
    (
        "value = helper.value\n",
        "alias = helper\nvalue = alias.value\n",
        "value = (alias := helper).value\n",
    ),
)
def test_python_inventory_rejects_local_fixture_reassigned_from_import(
    reassignment: str,
) -> None:
    resolver = guard._python_import_resolver(
        lambda path: (
            "def value(): return 'imported'\n" if path == "tests/helper.py" else None
        )
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="imported Python fixture name is ambiguous",
    ):
        guard._python_inventory_entries(
            "tests/test_example.py",
            "import pytest\n"
            "import tests.helper as helper\n"
            "@pytest.fixture\n"
            "def value(): return 'local'\n"
            + reassignment
            + "def test_case(value): pass\n",
            resolver,
        )


def test_python_inventory_rejects_class_local_requested_fixture() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="class-local pytest fixtures",
    ):
        guard.parse_python_declarations(
            "tests/test_example.py",
            "import pytest\n"
            "class TestCases:\n"
            "    @pytest.fixture\n"
            "    def value(self): return True\n"
            "    def test_case(self, value): pass\n",
        )


@pytest.mark.parametrize(
    "fixture_binding",
    (
        "    value = pytest.fixture(value)\n",
        "    fixture_factory = pytest.fixture()\n    value = fixture_factory(value)\n",
        "    target = value\n    value = pytest.fixture(target)\n",
        "    target, other = value, None\n    value = pytest.fixture(target)\n",
        "    fixture_factory = pytest.fixture\n    value = fixture_factory(value)\n",
    ),
)
def test_python_inventory_rejects_assigned_class_local_fixture(
    fixture_binding: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="class-local pytest fixtures",
    ):
        guard.parse_python_declarations(
            "tests/test_example.py",
            "import pytest\n"
            "class TestCases:\n"
            "    def value(self): return True\n"
            + fixture_binding
            + "    def test_case(self, value): pass\n",
        )


def test_python_inventory_rejects_inherited_class_local_fixture() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="class-local pytest fixtures",
    ):
        guard.parse_python_declarations(
            "tests/test_example.py",
            "import pytest\n"
            "class FixtureBase:\n"
            "    @pytest.fixture\n"
            "    def value(self): return True\n"
            "class TestCases(FixtureBase):\n"
            "    def test_case(self, value): pass\n",
        )


def test_changed_module_local_fixture_import_dependency_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "test_case.py").write_text(
        "import pytest\n"
        "from tests.fixture_helper import fixture_value\n"
        "@pytest.fixture\n"
        "def value(): return fixture_value()\n"
        "def test_case(value): pass\n"
    )
    (tests_root / "fixture_helper.py").write_text(
        "def fixture_value(): return 'current'\n"
    )
    outputs = iter((b"tests/fixture_helper.py\0", b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "def fixture_value(): return 'prior'\n"
            if path == "tests/fixture_helper.py"
            else (tmp_path / path).read_text()
            if (tmp_path / path).is_file()
            else None
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base: {
            "tests/fixture_helper.py",
            "tests/test_case.py",
        },
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed module-local pytest fixture dependency",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_application_subject_used_by_module_local_fixture_is_inventoried(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "test_case.py").write_text(
        "import pytest\n"
        "from ultimate_ai_agent.subject import fixture_value\n"
        "@pytest.fixture\n"
        "def value(): return fixture_value()\n"
        "def test_case(value): pass\n"
    )
    source_root = tmp_path / "src/ultimate_ai_agent"
    source_root.mkdir(parents=True)
    (source_root / "__init__.py").write_text("")
    (source_root / "subject.py").write_text("def fixture_value(): return 'current'\n")
    outputs = iter(
        (
            b"src/ultimate_ai_agent/subject.py\0",
            b"",
            b"",
            b"",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )

    assert guard._changed_test_paths(tmp_path, "a" * 40) == ("tests/test_case.py",)


def test_changed_unrelated_import_in_module_with_local_fixture_is_inventoried(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "test_case.py").write_text(
        "import pytest\n"
        "from tests.fixture_helper import fixture_value\n"
        "from tests.unrelated_helper import unrelated_value\n"
        "@pytest.fixture\n"
        "def value(): return fixture_value()\n"
        "def test_case(value): assert value != unrelated_value()\n"
    )
    (tests_root / "fixture_helper.py").write_text(
        "def fixture_value(): return 'stable'\n"
    )
    (tests_root / "unrelated_helper.py").write_text(
        "def unrelated_value(): return 'current'\n"
    )
    outputs = iter(
        (
            b"tests/unrelated_helper.py\0",
            b"",
            b"",
            b"",
            b"tests/fixture_helper.py\0tests/test_case.py\0tests/unrelated_helper.py\0",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "def unrelated_value(): return 'prior'\n"
            if path == "tests/unrelated_helper.py"
            else (tmp_path / path).read_text()
            if (tmp_path / path).is_file()
            else None
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_file_paths",
        lambda _repo, _base: {
            "tests/fixture_helper.py",
            "tests/test_case.py",
            "tests/unrelated_helper.py",
        },
    )

    assert guard._changed_test_paths(tmp_path, "a" * 40) == ("tests/test_case.py",)


def test_python_inventory_binds_autouse_fixture_package_initializer() -> None:
    test_source = (
        "import pytest\n"
        "import tests.pkg.helper as helper_module\n"
        "def run_setup(module): module.setup_environment()\n"
        "@pytest.fixture(autouse=True)\n"
        "def environment(): run_setup(helper_module)\n"
        "def test_case(): pass\n"
    )

    def refs_for(enabled: bool) -> tuple[str, ...]:
        resolver = guard._python_import_resolver(
            lambda path: (
                "import sys\n"
                "def setup_environment(): return sys.modules[__package__].ENABLED\n"
                if path == "tests/pkg/helper.py"
                else f"ENABLED = {enabled!r}\n"
                if path == "tests/pkg/__init__.py"
                else None
            )
        )
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_example.py",
                test_source,
                resolver,
            )
        )

    assert refs_for(True) != refs_for(False)


def test_python_inventory_binds_package_initializer_dependency_closure() -> None:
    test_source = (
        "import pytest\n"
        "import tests.pkg.helper as helper_module\n"
        "def run_setup(module): module.setup_environment()\n"
        "@pytest.fixture(autouse=True)\n"
        "def environment(): run_setup(helper_module)\n"
        "def test_case(): pass\n"
    )

    def refs_for(enabled: bool) -> tuple[str, ...]:
        resolver = guard._python_import_resolver(
            lambda path: (
                "import sys\n"
                "def setup_environment(): return sys.modules[__package__].ENABLED\n"
                if path == "tests/pkg/helper.py"
                else "from tests.pkg.state import ENABLED\n"
                if path == "tests/pkg/__init__.py"
                else f"ENABLED = {enabled!r}\n"
                if path == "tests/pkg/state.py"
                else None
            )
        )
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_example.py",
                test_source,
                resolver,
            )
        )

    assert refs_for(True) != refs_for(False)


@pytest.mark.parametrize(
    "dynamic_import",
    (
        'import importlib\nMODULE = importlib.import_module("tests.state")\n',
        'MODULE = __import__("tests.state", fromlist=("enabled",))\n',
    ),
)
def test_python_inventory_binds_literal_dynamic_autouse_module_dependencies(
    dynamic_import: str,
) -> None:
    test_source = (
        "import pytest\n"
        "import tests.helper as helper_module\n"
        "def run_setup(module): module.setup_environment()\n"
        "@pytest.fixture(autouse=True)\n"
        "def environment(): run_setup(helper_module)\n"
        "def test_case(): pass\n"
    )

    def refs_for(enabled: bool) -> tuple[str, ...]:
        resolver = guard._python_import_resolver(
            lambda path: (
                dynamic_import + "def setup_environment(): return MODULE.enabled\n"
                if path == "tests/helper.py"
                else f"enabled = {enabled!r}\n"
                if path == "tests/state.py"
                else None
            )
        )
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_example.py",
                test_source,
                resolver,
            )
        )

    assert refs_for(True) != refs_for(False)


def test_python_inventory_rejects_unresolved_dynamic_autouse_module_dependency() -> (
    None
):
    test_source = (
        "import pytest\n"
        "import tests.helper as helper_module\n"
        "def run_setup(module): module.setup_environment()\n"
        "@pytest.fixture(autouse=True)\n"
        "def environment(): run_setup(helper_module)\n"
        "def test_case(): pass\n"
    )
    resolver = guard._python_import_resolver(
        lambda path: (
            "import importlib\n"
            'TARGET = "tests.state"\n'
            "MODULE = importlib.import_module(TARGET)\n"
            "def setup_environment(): return MODULE.enabled\n"
            if path == "tests/helper.py"
            else None
        )
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic Python module dependencies",
    ):
        guard._python_inventory_entries(
            "tests/test_example.py",
            test_source,
            resolver,
        )


@pytest.mark.parametrize(
    "helper_source",
    (
        'MODULE = __import__("tests.pkg", fromlist=(DYNAMIC,))\n',
        "import importlib\n"
        'MODULE = importlib.import_module(".state", package=DYNAMIC)\n',
    ),
)
def test_python_inventory_rejects_nonstatic_dynamic_import_components(
    helper_source: str,
) -> None:
    resolver = guard._python_import_resolver(
        lambda path: (
            "DYNAMIC = 'state'\n"
            + helper_source
            + "def setup_environment(): return MODULE.enabled\n"
            if path == "tests/helper.py"
            else None
        )
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic Python module dependencies",
    ):
        guard._python_module_dependency_identity(
            "tests.helper",
            "path=tests/helper.py\nDYNAMIC = 'state'\n" + helper_source,
            resolver,
        )


@pytest.mark.parametrize(
    "helper_source",
    (
        "from builtins import __import__ as load\n"
        'MODULE = load("tests.state", fromlist=("enabled",))\n',
        "load, unused = __import__, None\n"
        'MODULE = load("tests.state", fromlist=("enabled",))\n',
        "import builtins\n"
        'MODULE = builtins.__import__("tests.state", fromlist=("enabled",))\n',
    ),
)
def test_python_module_identity_binds_builtin_importer_aliases(
    helper_source: str,
) -> None:
    def identity_for(enabled: bool) -> str:
        resolver = guard._python_import_resolver(
            lambda path: (
                f"enabled = {enabled!r}\n" if path == "tests/state.py" else None
            )
        )
        return guard._python_module_dependency_identity(
            "tests.helper",
            "path=tests/helper.py\n" + helper_source,
            resolver,
        )

    assert identity_for(True) != identity_for(False)


@pytest.mark.parametrize(
    "helper_source",
    (
        'MODULE = __import__("state", {"__package__": "tests.other"}, '
        '{}, ("enabled",), 1)\n',
        'MODULE = __import__("tests.pkg", fromlist=("*",))\n',
    ),
)
def test_python_inventory_rejects_unsafe_builtin_import_context(
    helper_source: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic Python module dependencies",
    ):
        guard._python_module_dependency_identity(
            "tests.helper",
            "path=tests/helper.py\n" + helper_source,
            guard._python_import_resolver(lambda _path: None),
        )


@pytest.mark.parametrize(
    "helper_source",
    (
        'MODULE = __import__("tests.pkg", fromlist=("state",))\n',
        "import importlib\n"
        'MODULE = importlib.import_module(".state", package="tests.pkg")\n',
    ),
)
def test_python_module_identity_binds_dynamic_submodule_dependencies(
    helper_source: str,
) -> None:
    def identity_for(enabled: bool) -> str:
        resolver = guard._python_import_resolver(
            lambda path: (
                f"enabled = {enabled!r}\n" if path == "tests/pkg/state.py" else None
            )
        )
        return guard._python_module_dependency_identity(
            "tests.pkg.helper",
            "path=tests/pkg/helper.py\n" + helper_source,
            resolver,
        )

    assert identity_for(True) != identity_for(False)


def test_python_module_identity_binds_grouped_lazy_export_target_source() -> None:
    package_source = (
        "path=tests/pkg/__init__.py\n"
        "from importlib import import_module\n"
        "_EXPORT_GROUPS = {'tests.target': {'value'}}\n"
        "def __getattr__(name):\n"
        "    module_name = next(iter(_EXPORT_GROUPS))\n"
        "    return getattr(import_module(module_name), name)\n"
    )

    def identity_for(enabled: bool) -> str:
        resolver = guard._python_import_resolver(
            lambda path: f"value = {enabled!r}\n" if path == "tests/target.py" else None
        )
        return guard._python_module_dependency_identity(
            "tests.pkg",
            package_source,
            resolver,
        )

    assert identity_for(True) != identity_for(False)


def test_python_module_identity_binds_grouped_lazy_export_dependency_closure() -> None:
    package_source = (
        "path=tests/pkg/__init__.py\n"
        "from importlib import import_module\n"
        "_EXPORT_GROUPS = {'tests.target': {'value'}}\n"
        "def __getattr__(name):\n"
        "    module_name = next(iter(_EXPORT_GROUPS))\n"
        "    return getattr(import_module(module_name), name)\n"
    )

    def identity_for(enabled: bool) -> str:
        resolver = guard._python_import_resolver(
            lambda path: (
                "from tests.state import value\n"
                if path == "tests/target.py"
                else f"value = {enabled!r}\n"
                if path == "tests/state.py"
                else None
            )
        )
        return guard._python_module_dependency_identity(
            "tests.pkg",
            package_source,
            resolver,
        )

    assert identity_for(True) != identity_for(False)


@pytest.mark.parametrize(
    "mutation",
    (
        '_EXPORT_GROUPS["tests.extra"] = {"value"}\n',
        '_EXPORT_GROUPS.update({"tests.extra": {"value"}})\n',
        '_groups = _EXPORT_GROUPS\n_groups["tests.extra"] = {"value"}\n',
        'globals()["_EXPORT_GROUPS"] = {"tests.extra": {"value"}}\n',
        'globals()["_EXPORT_GROUPS"]["tests.extra"] = {"value"}\n',
        'globals()["_EXPORT_GROUPS"].update({"tests.extra": {"value"}})\n',
        'globals()["_EXPORT_" + "GROUPS"].update({"tests.extra": {"value"}})\n',
        'export_name = "_EXPORT_GROUPS"\n'
        'globals()[export_name].update({"tests.extra": {"value"}})\n',
        'export_name = "_EXPORT_GROUPS"\n'
        'globals()[export_name] = {"tests.extra": {"value"}}\n',
        'export_name = "_EXPORT_GROUPS"\ndel globals()[export_name]\n',
        'globals().get("_EXPORT_GROUPS").update({"tests.extra": {"value"}})\n',
        'globals().get("_EXPORT_" + "GROUPS").update({"tests.extra": {"value"}})\n',
        'globals().get(export_name).update({"tests.extra": {"value"}})\n',
        'globals().__getitem__("_EXPORT_GROUPS").update({"tests.extra": {"value"}})\n',
        'globals().update({"_EXPORT_GROUPS": {"tests.extra": {"value"}}})\n',
        'globals().setdefault("_EXPORT_GROUPS", {"tests.extra": {"value"}})\n',
        'globals().pop("_EXPORT_GROUPS")\n',
    ),
)
def test_python_module_identity_rejects_grouped_lazy_export_mutation(
    mutation: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="lazy Python export modules",
    ):
        guard._python_module_dependency_identity(
            "tests.pkg",
            "path=tests/pkg/__init__.py\n"
            '_EXPORT_GROUPS = {"tests.target": {"value"}}\n' + mutation,
            guard._python_import_resolver(lambda _path: None),
        )


def test_python_inventory_rejects_dynamic_module_pytestmark_attribute() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic module attributes",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "import pytest\n"
            "def __getattr__(name):\n"
            "    if name == 'pytestmark':\n"
            "        return pytest.mark.skip\n"
            "    raise AttributeError(name)\n"
            "def test_case(): pass\n",
        )


def test_python_module_identity_allows_bounded_lazy_export_cache_write() -> None:
    source = (
        "path=tests/pkg/__init__.py\n"
        "from importlib import import_module\n"
        "_EXPORT_GROUPS = {'tests.target': {'value'}}\n"
        "_LAZY_EXPORTS = {\n"
        "    name: module_name\n"
        "    for module_name, names in _EXPORT_GROUPS.items()\n"
        "    for name in names\n"
        "}\n"
        "def __getattr__(name):\n"
        "    module_name = _LAZY_EXPORTS.get(name)\n"
        "    if module_name is None:\n"
        "        raise AttributeError(name)\n"
        "    value = getattr(import_module(module_name), name)\n"
        "    globals()[name] = value\n"
        "    return value\n"
    )

    identity = guard._python_module_dependency_identity(
        "tests.pkg",
        source,
        guard._python_import_resolver(
            lambda path: "value = True\n" if path == "tests/target.py" else None
        ),
    )

    assert "module=tests.target" in identity


@pytest.mark.parametrize(
    "cache_source",
    (
        'from importlib import import_module\n_LAZY_EXPORTS = {"extra": '
        '"tests.extra"}\n'
        "def __getattr__(name):\n"
        "    module_name = _LAZY_EXPORTS.get(name)\n"
        "    if module_name is None:\n"
        "        raise AttributeError(name)\n"
        "    value = getattr(import_module(module_name), name)\n"
        "    globals()[name] = value\n"
        "    return value\n",
        "_LAZY_EXPORTS = {\n"
        "    name: module_name\n"
        "    for module_name, names in _EXPORT_GROUPS.items()\n"
        "    for name in names\n"
        "}\n"
        "def import_module(_module_name):\n"
        '    return __import__("tests.extra")\n'
        "def __getattr__(name):\n"
        "    module_name = _LAZY_EXPORTS.get(name)\n"
        "    if module_name is None:\n"
        "        raise AttributeError(name)\n"
        "    value = getattr(import_module(module_name), name)\n"
        "    globals()[name] = value\n"
        "    return value\n",
        "from importlib import import_module\n"
        "_LAZY_EXPORTS = {\n"
        "    name: module_name\n"
        "    for module_name, names in _EXPORT_GROUPS.items()\n"
        "    for name in names\n"
        "}\n"
        "def __getattr__(name):\n"
        "    module_name = _LAZY_EXPORTS.get(name)\n"
        "    if module_name is None:\n"
        "        raise AttributeError(name)\n"
        "    value = getattr(import_module(module_name), name)\n"
        '    value = {"tests.extra": {"value"}}\n'
        "    globals()[name] = value\n"
        "    return value\n",
        'key = "_EXPORT_GROUPS"\nvars()[key]["tests.extra"] = {"value"}\n',
        'key = "_EXPORT_GROUPS"\nlocals()[key]["tests.extra"] = {"value"}\n',
    ),
)
def test_python_module_identity_rejects_lazy_export_cache_mutation(
    cache_source: str,
) -> None:
    source = (
        "path=tests/pkg/__init__.py\n"
        '_EXPORT_GROUPS = {"tests.target": {"value"}}\n' + cache_source
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="lazy Python export modules",
    ):
        guard._python_module_dependency_identity(
            "tests.pkg",
            source,
            guard._python_import_resolver(
                lambda path: "value = True\n" if path == "tests/target.py" else None
            ),
        )


def test_python_inventory_rejects_unresolved_fixture_factory_callable() -> None:
    source = (
        "import pytest\n"
        'value = pytest.fixture(name="value")(lambda: None)\n'
        "def test_case(value): pass\n"
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="fixture callable cannot be inventoried safely",
    ):
        guard.parse_python_declarations("tests/test_case.py", source)


def test_python_inventory_rejects_named_unresolved_fixture_factory_callable() -> None:
    source = (
        "import pytest\n"
        "implementation = lambda: None\n"
        'value = pytest.fixture(name="value")(implementation)\n'
        "def test_case(value): pass\n"
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="fixture callable cannot be inventoried safely",
    ):
        guard.parse_python_declarations("tests/test_case.py", source)


def test_python_inventory_binds_static_getfixturevalue_request() -> None:
    def refs_for(body: str) -> tuple[str, ...]:
        source = (
            "import pytest\n"
            "@pytest.fixture\n"
            f"def environment(): {body}\n"
            "def test_case(request):\n"
            '    request.getfixturevalue("environment")\n'
        )
        return tuple(
            declaration.ref
            for declaration in guard.parse_python_declarations(
                "tests/test_case.py",
                source,
            )
        )

    assert refs_for("return True") != refs_for('pytest.skip("disabled")')


def test_python_inventory_binds_aliased_getfixturevalue_request() -> None:
    def refs_for(body: str) -> tuple[str, ...]:
        source = (
            "import pytest\n"
            "@pytest.fixture\n"
            f"def environment(): {body}\n"
            "def test_case(request):\n"
            "    lookup = request.getfixturevalue\n"
            '    lookup("environment")\n'
        )
        return tuple(
            declaration.ref
            for declaration in guard.parse_python_declarations(
                "tests/test_case.py",
                source,
            )
        )

    assert refs_for("return True") != refs_for('pytest.skip("disabled")')


def test_python_inventory_rejects_dynamic_getfixturevalue_request() -> None:
    source = (
        "def test_case(request, fixture_name):\n"
        "    request.getfixturevalue(fixture_name)\n"
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic Python fixture request",
    ):
        guard.parse_python_declarations("tests/test_case.py", source)


def test_python_inventory_binds_imported_skipif_condition() -> None:
    test_source = (
        "import pytest\n"
        "from tests.flags import DISABLED\n"
        '@pytest.mark.skipif(DISABLED, reason="disabled")\n'
        "def test_case(): pass\n"
    )

    def refs_for(disabled: bool) -> tuple[str, ...]:
        resolver = guard._python_import_resolver(
            lambda path: (
                f"DISABLED = {disabled!r}\n" if path == "tests/flags.py" else None
            )
        )
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_case.py",
                test_source,
                resolver,
            )
        )

    assert refs_for(False) != refs_for(True)


def test_python_inventory_binds_imported_skipif_condition_through_local_alias() -> None:
    test_source = (
        "import pytest\n"
        "from tests.flags import FLAG\n"
        "DISABLED = FLAG\n"
        '@pytest.mark.skipif(DISABLED, reason="disabled")\n'
        "def test_case(): pass\n"
    )

    def refs_for(disabled: bool) -> tuple[str, ...]:
        resolver = guard._python_import_resolver(
            lambda path: f"FLAG = {disabled!r}\n" if path == "tests/flags.py" else None
        )
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_case.py",
                test_source,
                resolver,
            )
        )

    assert refs_for(False) != refs_for(True)


def test_python_inventory_binds_local_side_effect_imports() -> None:
    test_source = "import tests.helper\ndef test_case(): pass\n"

    def refs_for(helper_source: str) -> tuple[str, ...]:
        resolver = guard._python_import_resolver(
            lambda path: helper_source if path == "tests/helper.py" else None
        )
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_case.py",
                test_source,
                resolver,
            )
        )

    assert refs_for("ENABLED = True\n") != refs_for(
        'import pytest\npytest.skip("disabled", allow_module_level=True)\n'
    )


@pytest.mark.parametrize(
    "test_source",
    (
        "from tests.helper import UNUSED\ndef test_case(): pass\n",
        "from tests import helper\ndef test_case(): pass\n",
    ),
)
def test_python_inventory_binds_from_import_side_effects(test_source: str) -> None:
    def refs_for(helper_source: str) -> tuple[str, ...]:
        resolver = guard._python_import_resolver(
            lambda path: helper_source if path == "tests/helper.py" else None
        )
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_case.py",
                test_source,
                resolver,
            )
        )

    assert refs_for("UNUSED = True\n") != refs_for(
        'import pytest\npytest.skip("disabled", allow_module_level=True)\n'
    )


def test_python_inventory_binds_transitive_side_effect_imports() -> None:
    test_source = "import tests.helper\ndef test_case(): pass\n"

    def refs_for(state_source: str) -> tuple[str, ...]:
        resolver = guard._python_import_resolver(
            lambda path: (
                "import tests.state\n"
                if path == "tests/helper.py"
                else state_source
                if path == "tests/state.py"
                else None
            )
        )
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_case.py",
                test_source,
                resolver,
            )
        )

    assert refs_for("ENABLED = True\n") != refs_for(
        'import pytest\npytest.skip("disabled", allow_module_level=True)\n'
    )


@pytest.mark.parametrize(
    "alias_source",
    (
        "from builtins import vars as namespace\n",
        "namespace = vars\n",
    ),
)
def test_python_module_identity_rejects_aliased_namespace_export_mutation(
    alias_source: str,
) -> None:
    source = (
        "path=tests/pkg/__init__.py\n"
        '_EXPORT_GROUPS = {"tests.target": {"value"}}\n'
        + alias_source
        + 'key = "_EXPORT_GROUPS"\n'
        + 'namespace()[key]["tests.extra"] = {"value"}\n'
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="lazy Python export modules",
    ):
        guard._python_module_dependency_identity(
            "tests.pkg",
            source,
            guard._python_import_resolver(
                lambda path: "value = True\n" if path == "tests/target.py" else None
            ),
        )


def test_python_inventory_binds_rebound_import_alias_as_local_data() -> None:
    test_source = (
        "import pytest\n"
        "from tests.helper import setup_environment\n"
        "@pytest.fixture(autouse=True)\n"
        "def environment(): setup_environment()\n"
        "def test_case(): pass\n"
    )

    def refs_for(value: str) -> tuple[str, ...]:
        resolver = guard._python_import_resolver(
            lambda path: (
                "import tests.state as data\n"
                f"data = [{value!r}]\n"
                "def setup_environment(): return data\n"
                if path == "tests/helper.py"
                else "enabled = True\n"
                if path == "tests/state.py"
                else None
            )
        )
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_example.py",
                test_source,
                resolver,
            )
        )

    assert refs_for("one") != refs_for("two")


def test_python_inventory_binds_imported_autouse_fixture_posture() -> None:
    test_source = (
        "from tests.helper import environment as setup_environment\n"
        "def test_case(): pass\n"
    )

    def refs_for(helper_source: str) -> tuple[str, ...]:
        resolver = guard._python_import_resolver(
            lambda path: helper_source if path == "tests/helper.py" else None
        )
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_example.py",
                test_source,
                resolver,
            )
        )

    ordinary = refs_for("def environment():\n    return None\n")
    autouse = refs_for(
        "import pytest\n"
        "@pytest.fixture(autouse=True)\n"
        "def environment():\n"
        "    pytest.skip('disabled')\n"
    )
    changed_body = refs_for(
        "import pytest\n"
        "@pytest.fixture(autouse=True)\n"
        "def environment():\n"
        "    return None\n"
    )

    assert ordinary != autouse
    assert autouse != changed_body


def test_python_inventory_rejects_conditional_imported_autouse_fixture() -> None:
    helper_source = (
        "import pytest\n@pytest.fixture(autouse=True)\n"
        "def environment():\n    pytest.skip('disabled')\n"
    )
    resolver = guard._python_import_resolver(
        lambda path: helper_source if path == "tests/helper.py" else None
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="conditional imported autouse",
    ):
        guard._python_inventory_entries(
            "tests/test_example.py",
            "if True:\n    from tests.helper import environment\n"
            "def test_case(): pass\n",
            resolver,
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "environment = environment",
        "environment = None",
        "original = environment\nenvironment = None\nenvironment = original",
    ),
)
def test_python_inventory_rejects_mutated_imported_autouse_fixture(
    mutation: str,
) -> None:
    helper_source = (
        "import pytest\n@pytest.fixture(autouse=True)\n"
        "def environment():\n    pytest.skip('disabled')\n"
    )
    resolver = guard._python_import_resolver(
        lambda path: helper_source if path == "tests/helper.py" else None
    )
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="mutated imported autouse",
    ):
        guard._python_inventory_entries(
            "tests/test_example.py",
            "from tests.helper import environment\n"
            f"{mutation}\n"
            "def test_case(): pass\n",
            resolver,
        )


def test_python_inventory_rejects_mutated_reexported_autouse_fixture() -> None:
    sources = {
        "tests/helper.py": "from tests.factory import environment\n",
        "tests/factory.py": (
            "import pytest\n@pytest.fixture(autouse=True)\n"
            "def environment():\n    return None\n"
        ),
    }
    resolver = guard._python_import_resolver(sources.get)

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="mutated imported autouse",
    ):
        guard._python_inventory_entries(
            "tests/test_example.py",
            "from tests.helper import environment\n"
            "environment = None\n"
            "def test_case(): pass\n",
            resolver,
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "from tests.other import environment",
        "def environment():\n    return None",
        "with manager() as environment:\n    pass",
        "try:\n    pass\nexcept Exception as environment:\n    pass",
    ),
)
def test_python_inventory_rejects_complete_imported_autouse_rebinding(
    mutation: str,
) -> None:
    helper_source = (
        "import pytest\n@pytest.fixture(autouse=True)\n"
        "def environment():\n    return None\n"
    )
    sources = {
        "tests/helper.py": helper_source,
        "tests/other.py": "def environment():\n    return None\n",
    }
    resolver = guard._python_import_resolver(sources.get)

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="mutated imported autouse",
    ):
        guard._python_inventory_entries(
            "tests/test_example.py",
            "from tests.helper import environment\n"
            f"{mutation}\n"
            "def test_case(): pass\n",
            resolver,
        )


def test_python_inventory_binds_module_qualified_imported_autouse_fixture() -> None:
    test_source = (
        "import tests.helper as h\nenvironment = h.environment\ndef test_case(): pass\n"
    )

    def ref_for(helper_source: str) -> str:
        resolver = guard._python_import_resolver(
            lambda path: helper_source if path == "tests/helper.py" else None
        )
        return guard._python_inventory_entries(
            "tests/test_example.py", test_source, resolver
        )[0][0].ref

    assert ref_for("def environment():\n    return None\n") != ref_for(
        "import pytest\n@pytest.fixture(autouse=True)\n"
        "def environment():\n    pytest.xfail('disabled')\n"
    )


@pytest.mark.parametrize(
    "helper_source",
    (
        "import tests.factory as f\nauto = f.auto\n"
        "@auto\ndef environment():\n    return None\n",
        "from tests.factory import auto\nmarker = auto\n"
        "@marker\ndef environment():\n    return None\n",
    ),
)
def test_python_inventory_rejects_copied_imported_autouse_factory_alias(
    helper_source: str,
) -> None:
    sources = {
        "tests/helper.py": helper_source,
        "tests/factory.py": "import pytest\nauto = pytest.fixture(autouse=True)\n",
    }
    resolver = guard._python_import_resolver(sources.get)

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="imported autouse pytest fixture marker",
    ):
        guard._python_inventory_entries(
            "tests/test_example.py",
            "from tests.helper import environment\ndef test_case(): pass\n",
            resolver,
        )


@pytest.mark.parametrize(
    "fixture_source",
    (
        "import pytest\nOPTIONS={'autouse': True}\n"
        "@pytest.fixture(**OPTIONS)\ndef environment():\n    return None\n",
        "import pytest\nOPTIONS={'autouse': True}\n"
        "environment = pytest.fixture(**OPTIONS)(environment)\n",
    ),
)
def test_python_inventory_rejects_dynamic_autouse_fixture_options(
    fixture_source: str,
) -> None:
    resolver = guard._python_import_resolver(
        lambda path: fixture_source if path == "tests/helper.py" else None
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="Python fixtures",
    ):
        guard._python_inventory_entries(
            "tests/test_example.py",
            "from tests.helper import environment\ndef test_case(): pass\n",
            resolver,
        )


def test_python_inventory_binds_direct_functional_autouse_fixture() -> None:
    test_source = "from tests.helper import environment\ndef test_case(): pass\n"

    def ref_for(body: str) -> str:
        resolver = guard._python_import_resolver(
            lambda path: (
                "import pytest\ndef environment():\n"
                f"    {body}\n"
                "environment = pytest.fixture(environment, autouse=True)\n"
                if path == "tests/helper.py"
                else None
            )
        )
        return guard._python_inventory_entries(
            "tests/test_example.py", test_source, resolver
        )[0][0].ref

    assert ref_for("return None") != ref_for("pytest.xfail('disabled')")


def test_python_inventory_rejects_lazy_imported_autouse_fixture() -> None:
    sources = {
        "tests/helper.py": (
            "import tests.real as real\n"
            "def __getattr__(name):\n"
            "    if name == 'environment':\n        return real.environment\n"
        ),
        "tests/real.py": "def environment():\n    return None\n",
    }
    resolver = guard._python_import_resolver(sources.get)

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic imported autouse",
    ):
        guard._python_inventory_entries(
            "tests/test_example.py",
            "from tests.helper import environment\ndef test_case(): pass\n",
            resolver,
        )


def test_python_inventory_rejects_imported_autouse_factory_alias() -> None:
    sources = {
        "tests/helper.py": (
            "from tests.factory import auto\n"
            "@auto\ndef environment():\n    return None\n"
        ),
        "tests/factory.py": "import pytest\nauto = pytest.fixture(autouse=True)\n",
    }
    resolver = guard._python_import_resolver(sources.get)

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="imported autouse pytest fixture marker",
    ):
        guard._python_inventory_entries(
            "tests/test_example.py",
            "from tests.helper import environment\ndef test_case(): pass\n",
            resolver,
        )


def test_worktree_inventory_rejects_imported_autouse_factory_alias(
    tmp_path: Path,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "test_example.py").write_text(
        "from tests.helper import environment\ndef test_case(): pass\n"
    )
    (tests_root / "helper.py").write_text(
        "from tests.factory import auto\n@auto\ndef environment():\n    return None\n"
    )
    (tests_root / "factory.py").write_text(
        "import pytest\nauto = pytest.fixture(autouse=True)\n"
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="imported autouse pytest fixture marker",
    ):
        guard.inventory_worktree(tmp_path)


def test_python_inventory_rejects_ambiguous_imported_autouse_fixture() -> None:
    helper_source = (
        "import pytest\n@pytest.fixture(autouse=True)\n"
        "def environment():\n    return None\n"
    )
    resolver = guard._python_import_resolver(
        lambda path: (
            helper_source
            if path in {"tests/helper.py", "tests/helper/__init__.py"}
            else None
        )
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="imported Python parameter data is ambiguous",
    ):
        guard._python_inventory_entries(
            "tests/test_example.py",
            "from tests.helper import environment\ndef test_case(): pass\n",
            resolver,
        )


def test_worktree_inventory_rejects_ambiguous_imported_autouse_fixture(
    tmp_path: Path,
) -> None:
    tests_root = tmp_path / "tests"
    package_root = tests_root / "helper"
    package_root.mkdir(parents=True)
    fixture_source = (
        "import pytest\n@pytest.fixture(autouse=True)\n"
        "def environment():\n    return None\n"
    )
    (tests_root / "test_example.py").write_text(
        "from tests.helper import environment\ndef test_case(): pass\n"
    )
    (tests_root / "helper.py").write_text(fixture_source)
    (package_root / "__init__.py").write_text(fixture_source)

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="imported Python parameter data is ambiguous",
    ):
        guard.inventory_worktree(tmp_path)


def test_python_inventory_keeps_later_import_as_active_binding() -> None:
    test_source = (
        "import pytest\n"
        "from tests.helper import setup_environment\n"
        "@pytest.fixture(autouse=True)\n"
        "def environment(): setup_environment()\n"
        "def test_case(): pass\n"
    )

    def refs_for(enabled: bool) -> tuple[str, ...]:
        resolver = guard._python_import_resolver(
            lambda path: (
                "data = ['local']\n"
                "import tests.state as data\n"
                "def setup_environment(): return data.enabled\n"
                if path == "tests/helper.py"
                else f"enabled = {enabled!r}\n"
                if path == "tests/state.py"
                else None
            )
        )
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_example.py",
                test_source,
                resolver,
            )
        )

    assert refs_for(True) != refs_for(False)


def test_python_inventory_binds_assigned_post_definition_autouse_fixture_source() -> (
    None
):
    active = guard.parse_python_declarations(
        "tests/test_example.py",
        "import pytest\n"
        "def environment(): yield\n"
        "environment = pytest.fixture(autouse=True)(environment)\n"
        "def test_case(): pass\n",
    )
    disabled = guard.parse_python_declarations(
        "tests/test_example.py",
        "import pytest\n"
        'def environment(): pytest.skip("disabled")\n'
        "environment = pytest.fixture(autouse=True)(environment)\n"
        "def test_case(): pass\n",
    )

    assert {declaration.ref for declaration in active} != {
        declaration.ref for declaration in disabled
    }


def test_has_fixture_declaration_resolves_post_definition_alias() -> None:
    assert guard._has_fixture_declaration(
        "import pytest\n"
        "def shared_value(): return 'one'\n"
        "target = shared_value\n"
        "shared_value = pytest.fixture(target)\n",
        "tests/conftest.py",
    )


def test_has_fixture_declaration_resolves_executed_compound_alias() -> None:
    assert guard._has_fixture_declaration(
        "import pytest\n"
        "def shared_value(): return 'one'\n"
        "if True:\n"
        "    target = shared_value\n"
        "shared_value = pytest.fixture(target)\n",
        "tests/conftest.py",
    )


@pytest.mark.parametrize("condition", ("True", "False"))
def test_pytest_conftest_imports_reject_conditional_posture(condition: str) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="conditional pytest conftest imports",
    ):
        guard._pytest_conftest_import_modules(
            f"if {condition}:\n    from tests.fixture_plugin import shared_value\n",
            "tests/conftest.py",
        )


def test_pytest_conftest_imports_include_imported_submodule_candidate() -> None:
    assert guard._pytest_conftest_import_modules(
        "from tests import fixture_plugin\n",
        "tests/conftest.py",
    ) == {"tests", "tests.fixture_plugin"}


@pytest.mark.parametrize(
    "fixture_declaration",
    (
        "@pytest.fixture(autouse=True)\n",
        "auto = pytest.fixture(autouse=True)\n@auto\n",
    ),
)
def test_python_inventory_rejects_class_local_autouse_fixture(
    fixture_declaration: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="class-local autouse pytest fixtures",
    ):
        guard.parse_python_declarations(
            "tests/test_example.py",
            "import pytest\n"
            "class TestCases:\n"
            + "".join(f"    {line}\n" for line in fixture_declaration.splitlines())
            + "    def environment(self): yield\n"
            "    def test_case(self): pass\n",
        )


def test_changed_registered_pytest_plugin_collection_hook_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "conftest.py").write_text(
        'pytest_plugins = ["tests.collection_plugin"]\n'
    )
    plugin_path = tests_root / "collection_plugin.py"
    plugin_path.write_text(
        "def pytest_generate_tests(metafunc):\n    metafunc.parametrize('value', [1])\n"
    )
    outputs = iter(
        (
            b"tests/collection_plugin.py\0",
            b"",
            b"",
            b"",
            b"tests/collection_plugin.py\0",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "def pytest_generate_tests(metafunc):\n"
            "    metafunc.parametrize('value', [1, 2])\n"
            if path == "tests/collection_plugin.py"
            else None
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed registered pytest collection hooks",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_transitive_registered_pytest_plugin_hook_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "conftest.py").write_text(
        'pytest_plugins = ["tests.collection_plugin"]\n'
    )
    (tests_root / "collection_plugin.py").write_text(
        "from tests.hook_helper import pytest_collection_modifyitems\n"
    )
    helper_path = tests_root / "hook_helper.py"
    helper_path.write_text(
        "def pytest_collection_modifyitems(items):\n    items.clear()\n"
    )
    outputs = iter(
        (
            b"tests/hook_helper.py\0",
            b"",
            b"",
            b"",
            b"tests/collection_plugin.py\0tests/hook_helper.py\0",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "def pytest_collection_modifyitems(items):\n    items[:] = items\n"
            if path == "tests/hook_helper.py"
            else None
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed registered pytest collection hooks",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_test_module_registered_plugin_fixture_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "test_case.py").write_text(
        'pytest_plugins = ("tests.fixture_plugin",)\ndef test_case(): pass\n'
    )
    plugin_path = tests_root / "fixture_plugin.py"
    plugin_path.write_text(
        "import pytest\n"
        "@pytest.fixture(autouse=True)\n"
        "def environment(): pytest.skip('disabled')\n"
    )
    outputs = iter(
        (
            b"tests/fixture_plugin.py\0",
            b"",
            b"",
            b"",
            b"tests/fixture_plugin.py\0",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "import pytest\n"
            "@pytest.fixture(autouse=True)\n"
            "def environment(): return None\n"
            if path == "tests/fixture_plugin.py"
            else None
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed registered autouse pytest fixtures",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_registered_plugin_package_initializer_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_root = tmp_path / "tests/pkg"
    package_root.mkdir(parents=True)
    (tmp_path / "tests/test_case.py").write_text(
        'pytest_plugins = ("tests.pkg.fixture_plugin",)\ndef test_case(): pass\n'
    )
    initializer_path = package_root / "__init__.py"
    initializer_path.write_text("ENABLED = False\n")
    (package_root / "fixture_plugin.py").write_text(
        "import pytest\n"
        "from tests.pkg import ENABLED\n"
        "@pytest.fixture(autouse=True)\n"
        "def environment():\n"
        "    if not ENABLED:\n"
        "        pytest.skip('disabled')\n"
    )
    outputs = iter(
        (
            b"tests/pkg/__init__.py\0",
            b"",
            b"",
            b"",
            b"tests/pkg/__init__.py\0tests/pkg/fixture_plugin.py\0",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "ENABLED = True\n" if path == "tests/pkg/__init__.py" else None
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed registered pytest dependency",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_registered_plugin_dynamic_import_dependency_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "conftest.py").write_text(
        'pytest_plugins = ("tests.fixture_plugin",)\n'
    )
    (tests_root / "fixture_plugin.py").write_text(
        "import importlib\n"
        "import pytest\n"
        'state = importlib.import_module("tests.state")\n'
        "@pytest.fixture(autouse=True)\n"
        "def environment():\n"
        "    if not state.enabled:\n"
        "        pytest.skip('disabled')\n"
    )
    (tests_root / "state.py").write_text("enabled = False\n")
    outputs = iter(
        (
            b"tests/state.py\0",
            b"",
            b"",
            b"",
            b"tests/state.py\0",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "enabled = True\n" if path == "tests/state.py" else None
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed registered pytest dependency",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_imported_conftest_collection_hook_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "conftest.py").write_text(
        "from tests.collection_plugin import pytest_collection_modifyitems\n"
    )
    plugin_path = tests_root / "collection_plugin.py"
    plugin_path.write_text(
        "def pytest_collection_modifyitems(items):\n    items.clear()\n"
    )
    outputs = iter(
        (
            b"tests/collection_plugin.py\0",
            b"",
            b"",
            b"",
            b"tests/collection_plugin.py\0",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "def pytest_collection_modifyitems(items):\n    items[:] = items\n"
            if path == "tests/collection_plugin.py"
            else None
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed registered pytest collection hooks",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_conftest_imported_parameterized_fixture_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "conftest.py").write_text(
        "from tests.fixture_plugin import shared_value\n"
    )
    fixture_path = tests_root / "fixture_plugin.py"
    fixture_path.write_text(
        "import pytest\n"
        '@pytest.fixture(params=["one"])\n'
        "def shared_value(request): return request.param\n"
    )
    outputs = iter(
        (
            b"tests/fixture_plugin.py\0",
            b"",
            b"",
            b"",
            b"tests/fixture_plugin.py\0",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "import pytest\n"
            '@pytest.fixture(params=["one", "two"])\n'
            "def shared_value(request): return request.param\n"
            if path == "tests/fixture_plugin.py"
            else None
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed registered parameterized pytest fixtures",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_conftest_module_imported_parameterized_fixture_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "conftest.py").write_text(
        "import tests.fixture_plugin as fixture_source\n"
        "shared_value = fixture_source.shared_value\n"
    )
    fixture_path = tests_root / "fixture_plugin.py"
    fixture_path.write_text(
        "import pytest\n"
        '@pytest.fixture(params=["one"])\n'
        "def shared_value(request): return request.param\n"
    )
    outputs = iter(
        (
            b"tests/fixture_plugin.py\0",
            b"",
            b"",
            b"",
            b"tests/fixture_plugin.py\0",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "import pytest\n"
            '@pytest.fixture(params=["one", "two"])\n'
            "def shared_value(request): return request.param\n"
            if path == "tests/fixture_plugin.py"
            else None
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed registered parameterized pytest fixtures",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_hidden_conftest_registered_plugin_collection_hook_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_root = tmp_path / "tests"
    hidden_root = tests_root / ".hidden"
    hidden_root.mkdir(parents=True)
    (hidden_root / "conftest.py").write_text(
        'pytest_plugins = ["tests.collection_plugin"]\n'
    )
    plugin_path = tests_root / "collection_plugin.py"
    plugin_path.write_text(
        "def pytest_generate_tests(metafunc):\n    metafunc.parametrize('value', [1])\n"
    )
    outputs = iter(
        (
            b"tests/collection_plugin.py\0",
            b"",
            b"",
            b"",
            b"tests/collection_plugin.py\0",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "def pytest_generate_tests(metafunc):\n"
            "    metafunc.parametrize('value', [1, 2])\n"
            if path == "tests/collection_plugin.py"
            else None
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed registered pytest collection hooks",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_registered_pytest_plugin_parameterized_fixture_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "conftest.py").write_text(
        'pytest_plugins = ["tests.collection_plugin"]\n'
    )
    plugin_path = tests_root / "collection_plugin.py"
    plugin_path.write_text(
        "import pytest\n"
        '@pytest.fixture(params=["one"])\n'
        "def shared_value(request): return request.param\n"
    )
    outputs = iter(
        (
            b"tests/collection_plugin.py\0",
            b"",
            b"",
            b"",
            b"tests/collection_plugin.py\0",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "import pytest\n"
            '@pytest.fixture(params=["one", "two"])\n'
            "def shared_value(request): return request.param\n"
            if path == "tests/collection_plugin.py"
            else None
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed registered parameterized pytest fixtures",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_registered_pytest_plugin_ordinary_fixture_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "conftest.py").write_text(
        'pytest_plugins = ["tests.fixture_plugin"]\n'
    )
    plugin_path = tests_root / "fixture_plugin.py"
    plugin_path.write_text(
        "import pytest\n@pytest.fixture\ndef shared_value(): return 'current'\n"
    )
    outputs = iter(
        (
            b"tests/fixture_plugin.py\0",
            b"",
            b"",
            b"",
            b"tests/fixture_plugin.py\0",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "import pytest\n@pytest.fixture\ndef shared_value(): return 'prior'\n"
            if path == "tests/fixture_plugin.py"
            else None
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed registered pytest fixtures",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_registered_pytest_fixture_helper_dependency_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "conftest.py").write_text(
        'pytest_plugins = ["tests.fixture_plugin"]\n'
    )
    (tests_root / "fixture_plugin.py").write_text(
        "import pytest\n"
        "from tests.fixture_helper import shared_value_impl\n"
        "@pytest.fixture\n"
        "def shared_value(): return shared_value_impl()\n"
    )
    helper_path = tests_root / "fixture_helper.py"
    helper_path.write_text("def shared_value_impl(): return 'current'\n")
    outputs = iter(
        (
            b"tests/fixture_helper.py\0",
            b"",
            b"",
            b"",
            b"tests/fixture_helper.py\0",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "def shared_value_impl(): return 'prior'\n"
            if path == "tests/fixture_helper.py"
            else None
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed registered pytest dependency",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_changed_application_subject_used_by_fixture_is_not_frozen(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "conftest.py").write_text(
        "import pytest\n"
        "from ultimate_ai_agent.subject import shared_value_impl\n"
        "@pytest.fixture\n"
        "def shared_value(): return shared_value_impl()\n"
    )
    source_root = tmp_path / "src/ultimate_ai_agent"
    source_root.mkdir(parents=True)
    (source_root / "__init__.py").write_text("")
    subject_path = source_root / "subject.py"
    subject_path.write_text("def shared_value_impl(): return 'current'\n")
    outputs = iter(
        (
            b"src/ultimate_ai_agent/subject.py\0",
            b"",
            b"",
            b"",
            b"src/ultimate_ai_agent/subject.py\0",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "def shared_value_impl(): return 'prior'\n"
            if path == "src/ultimate_ai_agent/subject.py"
            else None
        ),
    )

    assert guard._changed_test_paths(tmp_path, "a" * 40) == ()


def test_changed_application_subject_pytest_hook_still_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_root = tmp_path / "tests"
    tests_root.mkdir()
    (tests_root / "conftest.py").write_text(
        "from ultimate_ai_agent.subject import pytest_collection_modifyitems\n"
    )
    source_root = tmp_path / "src/ultimate_ai_agent"
    source_root.mkdir(parents=True)
    (source_root / "__init__.py").write_text("")
    subject_path = source_root / "subject.py"
    subject_path.write_text(
        "def pytest_collection_modifyitems(items):\n    items.clear()\n"
    )
    outputs = iter(
        (
            b"src/ultimate_ai_agent/subject.py\0",
            b"",
            b"",
            b"",
            b"src/ultimate_ai_agent/subject.py\0",
        )
    )
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(
        guard,
        "_base_text",
        lambda _repo, _base, path: (
            "def pytest_collection_modifyitems(items):\n    items[:] = items\n"
            if path == "src/ultimate_ai_agent/subject.py"
            else None
        ),
    )

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed registered pytest collection hooks",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


def test_control_center_tests_helpers_are_not_test_files(tmp_path: Path) -> None:
    tests_root = tmp_path / "apps/control-center/tests"
    tests_root.mkdir(parents=True)
    (tests_root / "ports.ts").write_text("export const port = 4173;\n")
    (tests_root / "example.spec.ts").write_text('test("case", () => {});\n')

    assert guard.discover_test_files(tmp_path) == (
        "apps/control-center/tests/example.spec.ts",
    )


def test_frontend_inventory_rejects_generic_glob_registration_import() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="frontend glob registration import",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            'const modules = import.meta.glob<Module>("./cases/*.ts", { eager: true });\n',
        )


def test_frontend_inventory_rejects_generic_direct_runner_call() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="generic frontend test registration",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            'test<{}>("generic direct", () => {});\n',
        )


@pytest.mark.parametrize(
    "source",
    (
        'eval(`test("dynamic eval", () => {})`);\n',
        'const register = eval; register(`test("aliased eval", () => {})`);\n',
        'new Function(`test("dynamic function", () => {})`)();\n',
        'globalThis["eval"](`test("computed eval", () => {})`);\n',
        'globalThis["Function"](`test("computed function", () => {})`)();\n',
        'globalThis?.["eval"](`test("optional computed eval", () => {})`);\n',
    ),
)
def test_frontend_inventory_rejects_dynamic_registration(source: str) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic frontend test registration",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            source,
        )


def test_python_inventory_rejects_unittest_case_skiptest_import() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="module-level unittest collection abort",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "from unittest.case import SkipTest\n"
            "raise SkipTest('disabled')\n"
            "def test_case(): pass\n",
        )


@pytest.mark.parametrize(
    "raise_statement",
    (
        "raise case.SkipTest('disabled')",
        "abort = case.SkipTest\nraise abort('disabled')",
    ),
)
def test_python_inventory_rejects_aliased_unittest_case_module_skiptest(
    raise_statement: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="module-level unittest collection abort",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            f"import unittest.case as case\n{raise_statement}\ndef test_case(): pass\n",
        )


def test_python_inventory_rejects_assigned_unittest_case_namespace_alias() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="module-level unittest collection abort",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "import unittest.case\n"
            "uc = unittest.case\n"
            "raise uc.SkipTest('disabled')\n"
            "def test_case(): pass\n",
        )


def test_python_inventory_rejects_aliased_unittest_skip_namespace() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="post-definition unittest skip mutation",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "class TestGroup:\n"
            "    def test_case(self): pass\n"
            "attrs = TestGroup.test_case.__dict__\n"
            "attrs['__unittest_skip__'] = True\n",
        )


def test_python_inventory_rejects_class_body_unittest_skip_state() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="class-body unittest skip state",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "import unittest\n"
            "class TestGroup(unittest.TestCase):\n"
            "    __unittest_skip__ = True\n"
            "    __unittest_skip_why__ = 'disabled'\n"
            "    def test_case(self): pass\n",
        )


def test_python_inventory_binds_imported_fixture_name_override() -> None:
    test_source = (
        "from tests.helper import _value\ndef test_case(value): assert value\n"
    )

    def refs_for(params: str) -> tuple[str, ...]:
        helper_source = (
            "import pytest\n"
            f"@pytest.fixture(name='value', params={params})\n"
            "def _value(request): return request.param\n"
        )
        resolver = guard._python_import_resolver(
            lambda path: helper_source if path == "tests/helper.py" else None
        )
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_sample.py",
                test_source,
                resolver,
            )
        )

    assert refs_for("[1, 2]") != refs_for("[1]")


def test_python_inventory_binds_aliased_imported_fixture_name_override() -> None:
    test_source = (
        "from tests.helper import _value\ndef test_case(value): assert value\n"
    )

    def refs_for(params: str) -> tuple[str, ...]:
        helper_source = (
            "from pytest import fixture as fx\n"
            f"@fx(name='value', params={params})\n"
            "def _value(request): return request.param\n"
        )
        resolver = guard._python_import_resolver(
            lambda path: helper_source if path == "tests/helper.py" else None
        )
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_sample.py",
                test_source,
                resolver,
            )
        )

    assert refs_for("[1, 2]") != refs_for("[1]")


def test_python_inventory_binds_assigned_pytest_fixture_namespace_alias() -> None:
    test_source = (
        "from tests.helper import _value\ndef test_case(value): assert value\n"
    )

    def refs_for(params: str) -> tuple[str, ...]:
        helper_source = (
            "import pytest as p\n"
            "q = p\n"
            f"@q.fixture(name='value', params={params})\n"
            "def _value(request): return request.param\n"
        )
        resolver = guard._python_import_resolver(
            lambda path: helper_source if path == "tests/helper.py" else None
        )
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_sample.py",
                test_source,
                resolver,
            )
        )

    assert refs_for("[1, 2]") != refs_for("[1]")


def test_imported_binding_identity_caches_transitive_closures() -> None:
    sources = {
        "tests/first.py": "from tests.shared import VALUE\nFIRST = VALUE\n",
        "tests/second.py": "from tests.shared import VALUE\nSECOND = VALUE\n",
        "tests/shared.py": "VALUE = ('stable', 1)\n",
    }
    resolver = guard._python_import_resolver(sources.get)

    first_source = resolver("tests.first")
    second_source = resolver("tests.second")

    assert first_source is not None
    assert second_source is not None
    guard._python_imported_binding_source(
        "tests.first",
        first_source,
        "FIRST",
        resolver,
    )
    binding_cache = getattr(resolver, "_uaa_binding_identity_cache")
    assert any(
        module == "tests.shared" and binding == "VALUE"
        for module, binding, _source_digest in binding_cache
    )
    assert any(
        module == "tests.first" and binding == "FIRST"
        for module, binding, _source_digest in binding_cache
    )
    cache_size = len(binding_cache)

    guard._python_imported_binding_source(
        "tests.second",
        second_source,
        "SECOND",
        resolver,
    )

    assert len(binding_cache) == cache_size + 1


def test_python_import_resolver_reuses_only_exact_source_trees() -> None:
    resolver = guard._python_import_resolver(lambda _path: None)

    first = guard._python_parsed_module("tests.helper", "VALUE = 1\n", resolver)
    repeated = guard._python_parsed_module("tests.helper", "VALUE = 1\n", resolver)
    changed = guard._python_parsed_module("tests.helper", "VALUE = 2\n", resolver)

    assert repeated is first
    assert changed is not first
    assert len(getattr(resolver, "_uaa_parsed_module_cache")) == 2


def test_imported_binding_analysis_reuses_only_exact_module_source() -> None:
    resolver = guard._python_import_resolver(lambda _path: None)
    first_source = "path=tests/helper.py\nFIRST = 1\nSECOND = 2\n"
    changed_source = "path=tests/helper.py\nFIRST = 3\nSECOND = 2\n"

    first = guard._python_imported_binding_source(
        "tests.helper",
        first_source,
        "FIRST",
        resolver,
    )
    second = guard._python_imported_binding_source(
        "tests.helper",
        first_source,
        "SECOND",
        resolver,
    )
    analysis_cache = getattr(resolver, "_uaa_binding_module_analysis_cache")

    assert first != second
    assert len(analysis_cache) == 1
    changed = guard._python_imported_binding_source(
        "tests.helper",
        changed_source,
        "FIRST",
        resolver,
    )
    assert changed != first
    assert len(analysis_cache) == 2


def test_imported_binding_analysis_reuses_shared_binding_nodes() -> None:
    resolver = guard._python_import_resolver(lambda _path: None)
    source = (
        "path=tests/helper.py\n"
        "SHARED = ('stable', 1)\n"
        "FIRST = SHARED\n"
        "SECOND = SHARED\n"
    )

    guard._python_imported_binding_source(
        "tests.helper",
        source,
        "FIRST",
        resolver,
    )
    module_analysis = next(
        iter(getattr(resolver, "_uaa_binding_module_analysis_cache").values())
    )
    cached_positions = set(module_analysis.node_analyses)

    guard._python_imported_binding_source(
        "tests.helper",
        source,
        "SECOND",
        resolver,
    )

    assert cached_positions.issubset(module_analysis.node_analyses)
    assert len(module_analysis.node_analyses) == len(cached_positions) + 1


def test_imported_binding_identity_caches_top_level_cycle_closures() -> None:
    sources = {
        "tests/first.py": "from tests.second import VALUE\nFIRST = VALUE\n",
        "tests/second.py": "from tests.first import FIRST\nVALUE = FIRST\n",
    }
    resolver = guard._python_import_resolver(sources.get)
    source = resolver("tests.first")

    assert source is not None
    first = guard._python_imported_binding_source(
        "tests.first",
        source,
        "FIRST",
        resolver,
    )
    cache = getattr(resolver, "_uaa_root_binding_identity_cache")
    assert any(
        module == "tests.first" and binding == "FIRST"
        for module, binding, _source_digest in cache
    )

    sources["tests/second.py"] = (
        "from tests.first import FIRST\nVALUE = ('changed', FIRST)\n"
    )
    second_resolver = guard._python_import_resolver(sources.get)
    second_source = second_resolver("tests.first")

    assert second_source is not None
    second = guard._python_imported_binding_source(
        "tests.first",
        second_source,
        "FIRST",
        second_resolver,
    )
    assert first != second


def test_imported_binding_identity_caches_forwarded_top_level_cycle() -> None:
    sources = {
        "tests/first.py": "from tests.second import FIRST\n",
        "tests/second.py": "from tests.first import FIRST\n",
    }
    resolver = guard._python_import_resolver(sources.get)
    source = resolver("tests.first")

    assert source is not None
    identity = guard._python_imported_binding_source(
        "tests.first",
        source,
        "FIRST",
        resolver,
    )
    cache = getattr(resolver, "_uaa_root_binding_identity_cache")

    assert "transitive-import-cycle" in identity
    assert any(
        module == "tests.first" and binding == "FIRST"
        for module, binding, _source_digest in cache
    )
    assert (
        guard._python_imported_binding_source(
            "tests.first",
            source,
            "FIRST",
            resolver,
        )
        == identity
    )


def test_python_inventory_binds_fixture_default_posture() -> None:
    active = guard.parse_python_declarations(
        "tests/test_sample.py",
        "def test_case(value): assert value\n",
    )
    defaulted = guard.parse_python_declarations(
        "tests/test_sample.py",
        "def test_case(value=None): assert value\n",
    )

    assert [item.ref for item in active] != [item.ref for item in defaulted]


def test_python_inventory_associates_fixture_defaults_with_argument_names() -> None:
    first = guard.parse_python_declarations(
        "tests/test_sample.py",
        "def test_case(*, a, b=None): pass\n",
    )
    second = guard.parse_python_declarations(
        "tests/test_sample.py",
        "def test_case(*, a=None, b): pass\n",
    )

    assert [item.ref for item in first] != [item.ref for item in second]


def test_frontend_dependency_paths_follow_commonjs_require() -> None:
    sources = {
        "apps/control-center/vitest.config.cjs": (
            'module.exports = require("./vitest.shared.cjs");\n'
        ),
        "apps/control-center/vitest.shared.cjs": "module.exports = {};\n",
    }

    dependencies = guard._frontend_dependency_paths(
        {"apps/control-center/vitest.config.cjs"},
        sources.get,
    )

    assert "apps/control-center/vitest.shared.cjs" in dependencies


def test_frontend_dependency_paths_follow_template_commonjs_require() -> None:
    sources = {
        "apps/control-center/vitest.config.cjs": (
            "module.exports = require(`./vitest.shared.cjs`);\n"
        ),
        "apps/control-center/vitest.shared.cjs": "module.exports = {};\n",
    }

    dependencies = guard._frontend_dependency_paths(
        {"apps/control-center/vitest.config.cjs"},
        sources.get,
    )

    assert "apps/control-center/vitest.shared.cjs" in dependencies


def test_frontend_dependency_paths_follow_optional_commonjs_require() -> None:
    sources = {
        "apps/control-center/vitest.config.cjs": (
            'module.exports = require?.("./vitest.shared.cjs");\n'
        ),
        "apps/control-center/vitest.shared.cjs": "module.exports = {};\n",
    }

    dependencies = guard._frontend_dependency_paths(
        {"apps/control-center/vitest.config.cjs"},
        sources.get,
    )

    assert "apps/control-center/vitest.shared.cjs" in dependencies


def test_frontend_dependency_paths_follow_parenthesized_commonjs_require() -> None:
    sources = {
        "apps/control-center/vitest.config.cjs": (
            'module.exports = (require)("./vitest.shared.cjs");\n'
        ),
        "apps/control-center/vitest.shared.cjs": "module.exports = {};\n",
    }

    dependencies = guard._frontend_dependency_paths(
        {"apps/control-center/vitest.config.cjs"},
        sources.get,
    )

    assert "apps/control-center/vitest.shared.cjs" in dependencies


@pytest.mark.parametrize("extension", ("json", "node", "css"))
def test_frontend_dependency_paths_preserve_explicit_commonjs_extension(
    extension: str,
) -> None:
    sources = {
        "apps/control-center/vitest.config.cjs": (
            f'module.exports = require("./vitest.shared.{extension}");\n'
        ),
        f"apps/control-center/vitest.shared.{extension}": "{}\n",
    }

    dependencies = guard._frontend_dependency_paths(
        {"apps/control-center/vitest.config.cjs"},
        sources.get,
    )

    assert dependencies == {f"apps/control-center/vitest.shared.{extension}"}


def test_frontend_dependency_paths_reject_dynamic_optional_commonjs_require() -> None:
    sources = {
        "apps/control-center/vitest.config.cjs": (
            'const modulePath = "./vitest.shared.cjs";\n'
            "module.exports = require?.(modulePath);\n"
        ),
    }

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic CommonJS dependency",
    ):
        guard._frontend_dependency_paths(
            {"apps/control-center/vitest.config.cjs"},
            sources.get,
        )


def test_frontend_dependency_paths_reject_aliased_commonjs_require() -> None:
    sources = {
        "apps/control-center/vitest.config.cjs": (
            'const load = require;\nmodule.exports = load("./vitest.shared.cjs");\n'
        ),
    }

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="dynamic CommonJS dependency",
    ):
        guard._frontend_dependency_paths(
            {"apps/control-center/vitest.config.cjs"},
            sources.get,
        )


def test_frontend_inventory_rejects_commonjs_registration_dependency() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="CommonJS registration dependency",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.cjs",
            'require("./helper.cjs");\n',
        )


def test_pytest_workflow_boundary_is_exact_to_collection_inputs() -> None:
    base = """env:
  PATH: /usr/bin
defaults:
  run:
    shell: bash
jobs:
  pytest-shards:
    steps:
      - run: python scripts/verification/run_ci_lane.py --lane ci-pytest-shards
  static-verification:
    steps:
      - uses: actions/checkout@pinned
        with:
          fetch-depth: 1
"""
    benign = base.replace("fetch-depth: 1", "fetch-depth: 0")
    dangerous = base.replace(
        "  pytest-shards:\n",
        "  pytest-shards:\n    env:\n      PYTEST_ADDOPTS: --deselect=tests/test_target.py\n",
    )

    assert guard._pytest_workflow_collection_boundary(
        base
    ) == guard._pytest_workflow_collection_boundary(benign)
    assert guard._pytest_workflow_collection_boundary(
        base
    ) != guard._pytest_workflow_collection_boundary(dangerous)


def test_python_inventory_rejects_string_skipif_condition() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="string skip condition",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "import pytest\n"
            'FLAG = "False"\n'
            '@pytest.mark.skipif("FLAG", reason="disabled")\n'
            "def test_case(): pass\n",
        )


@pytest.mark.parametrize(
    "source",
    (
        "import pytest\n"
        "class Helper:\n"
        '    pytest.skip("disabled", allow_module_level=True)\n'
        "def test_case(): pass\n",
        "import pytest\n"
        "def stop():\n"
        '    pytest.skip("disabled", allow_module_level=True)\n'
        "stop()\n"
        "def test_case(): pass\n",
        "import pytest\n"
        'OPTIONS = {"allow_module_level": True}\n'
        'pytest.skip("disabled", **OPTIONS)\n'
        "def test_case(): pass\n",
    ),
)
def test_python_inventory_rejects_transitive_collection_aborts(
    source: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="module-level pytest collection abort",
    ):
        guard.parse_python_declarations("tests/test_sample.py", source)


def test_python_inventory_rejects_callable_alias_collection_abort() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="module-level pytest collection abort",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "import pytest\n"
            "def stop():\n"
            '    pytest.skip("disabled", allow_module_level=True)\n'
            "abort = stop\n"
            "abort()\n"
            "def test_case(): pass\n",
        )


@pytest.mark.parametrize("hook_name", ("setUp", "setUpClass"))
def test_python_inventory_rejects_unittest_lifecycle_hooks(
    hook_name: str,
) -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="unittest lifecycle hooks",
    ):
        guard.parse_python_declarations(
            "tests/test_sample.py",
            "import unittest\n"
            "class TestCase(unittest.TestCase):\n"
            f"    def {hook_name}(self): pass\n"
            "    def test_case(self): pass\n",
        )


def test_frontend_inventory_binds_static_test_options() -> None:
    def ref_for(skip: bool) -> str:
        return guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            f'test("case", {{ skip: {str(skip).lower()} }}, () => {{}});\n',
        )[0].ref

    assert ref_for(False) != ref_for(True)


def test_frontend_inventory_binds_named_static_test_options() -> None:
    def ref_for(skip: bool) -> str:
        return guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            f"const OPTIONS = {{ skip: {str(skip).lower()} }};\n"
            'test("case", OPTIONS, () => {});\n',
        )[0].ref

    assert ref_for(False) != ref_for(True)


def test_frontend_inventory_rejects_dynamic_test_options() -> None:
    with pytest.raises(
        guard.TestCorpusGuardError,
        match="test option object",
    ):
        guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            'test("case", buildOptions(), () => {});\n',
        )


def test_frontend_inventory_binds_inherited_suite_options() -> None:
    def ref_for(skip: bool) -> str:
        return guard.parse_frontend_declarations(
            "apps/control-center/src/example.test.ts",
            'describe("suite", '
            f"{{ skip: {str(skip).lower()} }}, "
            '() => { test("case", () => {}); });\n',
        )[0].ref

    assert ref_for(False) != ref_for(True)


def test_python_inventory_rejects_match_capture_of_imported_autouse_fixture() -> None:
    sources = {
        "tests/helper.py": (
            "import pytest\n@pytest.fixture(autouse=True)\n"
            "def environment():\n    return None\n"
        )
    }
    resolver = guard._python_import_resolver(sources.get)

    with pytest.raises(guard.TestCorpusGuardError, match="autouse|fixture"):
        guard._python_inventory_entries(
            "tests/test_example.py",
            "from tests.helper import environment\nvalue = None\n"
            "match value:\n    case environment:\n        pass\n"
            "def test_case(): pass\n",
            resolver,
        )


@pytest.mark.parametrize(
    "suffix",
    (
        "environment = None\n",
        "FLAG = False\nif FLAG:\n    environment = helper.environment\n",
    ),
)
def test_python_inventory_rejects_ambiguous_qualified_autouse_assignment(
    suffix: str,
) -> None:
    resolver = guard._python_import_resolver(
        lambda path: (
            "import pytest\n@pytest.fixture(autouse=True)\n"
            "def environment():\n    return None\n"
            if path == "tests/helper.py"
            else None
        )
    )
    source = (
        "import tests.helper as helper\n"
        "environment = helper.environment\n"
        f"{suffix}def test_case(): pass\n"
    )

    with pytest.raises(guard.TestCorpusGuardError, match="autouse|fixture|binding"):
        guard._python_inventory_entries("tests/test_example.py", source, resolver)


@pytest.mark.parametrize(
    "helper_source",
    (
        "import tests.real as real\n__getattr__ = lambda name: real.environment\n",
        "_LAZY_EXPORT_MODULES = {'environment': 'tests.real'}\n"
        "def __getattr__(name):\n    return None\n",
    ),
)
def test_python_inventory_rejects_or_binds_all_lazy_autouse_forms(
    helper_source: str,
) -> None:
    sources = {
        "tests/helper.py": helper_source,
        "tests/real.py": (
            "import pytest\n@pytest.fixture(autouse=True)\n"
            "def environment():\n    pytest.xfail('disabled')\n"
        ),
    }
    resolver = guard._python_import_resolver(sources.get)

    with pytest.raises(guard.TestCorpusGuardError, match="autouse|fixture|dynamic"):
        guard._python_inventory_entries(
            "tests/test_example.py",
            "from tests.helper import environment\ndef test_case(): pass\n",
            resolver,
        )


def test_python_inventory_binds_local_functional_autouse_factory_alias() -> None:
    def ref_for(body: str) -> str:
        return guard.parse_python_declarations(
            "tests/test_example.py",
            "import pytest\nauto = pytest.fixture(autouse=True)\n"
            f"def setup():\n    {body}\n"
            "environment = auto(setup)\ndef test_case(): pass\n",
        )[0].ref

    assert ref_for("return None") != ref_for("pytest.xfail('disabled')")


@pytest.mark.parametrize(
    "test_source",
    (
        "from tests.helper import stop\ndef test_case():\n"
        "    alias = stop\n    alias()\n",
        "import tests.helper as helper\ndef test_case():\n"
        "    alias = helper.stop\n    alias()\n",
    ),
)
def test_python_inventory_binds_imported_runtime_helper_alias(
    test_source: str,
) -> None:
    def ref_for(body: str) -> str:
        resolver = guard._python_import_resolver(
            lambda path: (
                f"def stop():\n    {body}\n" if path == "tests/helper.py" else None
            )
        )
        return guard._python_inventory_entries(
            "tests/test_example.py", test_source, resolver
        )[0][0].ref

    assert ref_for("return None") != ref_for("import pytest; pytest.xfail('disabled')")


@pytest.mark.parametrize(
    "local_binding",
    (
        "path = tmp_path\n    path.as_posix()",
        "for path in (tmp_path,):\n        path.as_posix()",
        "with nullcontext(tmp_path) as path:\n        path.as_posix()",
        "try:\n        raise RuntimeError\n"
        "    except RuntimeError as path:\n        path.add_note('handled')",
        "import pathlib as path\n    path.Path('.')",
        "match {'path': tmp_path}:\n"
        "        case {'path': path}:\n            path.as_posix()",
        "def path():\n        return None\n    path()",
        "class path:\n        pass\n    path()",
    ),
)
def test_python_inventory_ignores_import_shadowed_by_local_binding(
    local_binding: str,
) -> None:
    def ref_for(body: str) -> str:
        resolver = guard._python_import_resolver(
            lambda path: (
                f"def as_posix():\n    {body}\n" if path == "tests/helper.py" else None
            )
        )
        return guard._python_inventory_entries(
            "tests/test_example.py",
            "from tests import helper as path\n"
            "from contextlib import nullcontext\n"
            "def test_case(tmp_path):\n"
            f"    {local_binding}\n",
            resolver,
        )[0][0].ref

    assert ref_for("return None") == ref_for("import pytest; pytest.xfail('disabled')")


@pytest.mark.parametrize(
    ("test_source", "depends_on_import"),
    (
        (
            "import tests.helper as path\n"
            "def prepare(tmp_path):\n"
            "    path = tmp_path\n"
            "    path.as_posix()\n"
            "def test_case(tmp_path):\n"
            "    prepare(tmp_path)\n",
            False,
        ),
        (
            "import tests.helper as path\n"
            "def test_case(tmp_path):\n"
            "    path = tmp_path\n"
            "    def invoke():\n"
            "        nonlocal path\n"
            "        path.as_posix()\n"
            "    invoke()\n",
            False,
        ),
        (
            "from tests import helper\n"
            "def test_case():\n"
            "    path = helper\n"
            "    def invoke():\n"
            "        nonlocal path\n"
            "        path.as_posix()\n"
            "    invoke()\n",
            True,
        ),
        (
            "import tests.helper as path\n"
            "def prepare():\n"
            "    global path\n"
            "    path.as_posix()\n"
            "def test_case():\n"
            "    prepare()\n",
            True,
        ),
        (
            "def test_case():\n    from tests.helper import stop\n    stop()\n",
            True,
        ),
        (
            "def test_case():\n    import tests.helper as helper\n    helper.stop()\n",
            True,
        ),
        (
            "def test_case():\n"
            "    import tests.helper as helper\n"
            "    def invoke():\n"
            "        nonlocal helper\n"
            "        helper.stop()\n"
            "    invoke()\n",
            True,
        ),
        (
            "def test_case():\n"
            "    import tests.helper as helper\n"
            "    def invoke():\n"
            "        helper.stop()\n"
            "    invoke()\n",
            True,
        ),
        (
            "def prepare():\n"
            "    global helper\n"
            "    import tests.helper as helper\n"
            "    helper.stop()\n"
            "def test_case():\n"
            "    prepare()\n",
            True,
        ),
        (
            "def prepare():\n"
            "    import tests.helper as helper\n"
            "def test_case():\n"
            "    helper.stop()\n",
            False,
        ),
        (
            "def prepare():\n"
            "    global helper\n"
            "    import tests.helper as helper\n"
            "def test_case():\n"
            "    prepare()\n"
            "    helper.stop()\n",
            True,
        ),
        (
            "def prepare():\n"
            "    global stop\n"
            "    from tests.helper import stop\n"
            "def test_case():\n"
            "    prepare()\n"
            "    stop()\n",
            True,
        ),
        (
            "def install():\n"
            "    global helper\n"
            "    import tests.helper as helper\n"
            "def wrapper():\n"
            "    install()\n"
            "def test_case():\n"
            "    wrapper()\n"
            "    helper.stop()\n",
            True,
        ),
    ),
)
def test_python_runtime_helper_imports_follow_lexical_scope(
    test_source: str,
    depends_on_import: bool,
) -> None:
    def ref_for(body: str) -> str:
        resolver = guard._python_import_resolver(
            lambda path: (
                f"def as_posix():\n    {body}\ndef stop():\n    {body}\n"
                if path == "tests/helper.py"
                else None
            )
        )
        return guard._python_inventory_entries(
            "tests/test_example.py",
            test_source,
            resolver,
        )[0][0].ref

    changed = ref_for("return None") != ref_for(
        "import pytest; pytest.xfail('disabled')"
    )
    assert changed is depends_on_import


def test_python_runtime_helper_relative_imports_stay_in_their_scope() -> None:
    test_source = (
        "def active():\n"
        "    from .helper import stop\n"
        "    stop()\n"
        "def dormant():\n"
        "    from .other import stop\n"
        "    stop()\n"
        "def test_case():\n"
        "    active()\n"
    )

    def ref_for(active_body: str, dormant_body: str) -> str:
        sources = {
            "tests/helper.py": f"def stop():\n    {active_body}\n",
            "tests/other.py": f"def stop():\n    {dormant_body}\n",
        }
        resolver = guard._python_import_resolver(sources.get)
        return guard._python_inventory_entries(
            "tests/test_example.py",
            test_source,
            resolver,
        )[0][0].ref

    baseline = ref_for("return None", "return None")
    assert baseline != ref_for(
        "import pytest; pytest.xfail('disabled')",
        "return None",
    )
    assert baseline == ref_for(
        "return None",
        "import pytest; pytest.xfail('disabled')",
    )


def test_python_runtime_global_import_install_replaces_module_binding() -> None:
    test_source = (
        "import tests.one as helper\n"
        "def install():\n"
        "    global helper\n"
        "    import tests.two as helper\n"
        "def test_case():\n"
        "    install()\n"
        "    helper.stop()\n"
    )

    def ref_for(one_body: str, two_body: str) -> str:
        sources = {
            "tests/one.py": f"def stop():\n    {one_body}\n",
            "tests/two.py": f"def stop():\n    {two_body}\n",
        }
        resolver = guard._python_import_resolver(sources.get)
        return guard._python_inventory_entries(
            "tests/test_example.py",
            test_source,
            resolver,
        )[0][0].ref

    baseline = ref_for("return None", "return None")
    assert baseline == ref_for(
        "import pytest; pytest.xfail('disabled')",
        "return None",
    )
    assert baseline != ref_for(
        "return None",
        "import pytest; pytest.xfail('disabled')",
    )


def test_python_runtime_global_import_install_preserves_each_used_version() -> None:
    test_source = (
        "def install_one():\n"
        "    global helper\n"
        "    import tests.one as helper\n"
        "def install_two():\n"
        "    global helper\n"
        "    import tests.two as helper\n"
        "def test_case():\n"
        "    install_one()\n"
        "    helper.stop()\n"
        "    install_two()\n"
        "    helper.stop()\n"
    )

    def ref_for(one_body: str, two_body: str) -> str:
        sources = {
            "tests/one.py": f"def stop():\n    {one_body}\n",
            "tests/two.py": f"def stop():\n    {two_body}\n",
        }
        resolver = guard._python_import_resolver(sources.get)
        return guard._python_inventory_entries(
            "tests/test_example.py",
            test_source,
            resolver,
        )[0][0].ref

    baseline = ref_for("return None", "return None")
    assert baseline != ref_for(
        "import pytest; pytest.xfail('disabled')",
        "return None",
    )
    assert baseline != ref_for(
        "return None",
        "import pytest; pytest.xfail('disabled')",
    )


def test_python_runtime_global_import_installers_fail_closed_in_branches() -> None:
    test_source = (
        "import pytest\n"
        "def install_one():\n"
        "    global helper\n"
        "    import tests.one as helper\n"
        "def install_two():\n"
        "    global helper\n"
        "    import tests.two as helper\n"
        "@pytest.mark.parametrize('flag', [True, False])\n"
        "def test_case(flag):\n"
        "    if flag:\n"
        "        install_one()\n"
        "    else:\n"
        "        install_two()\n"
        "    helper.stop()\n"
    )
    sources = {
        "tests/one.py": "def stop():\n    return None\n",
        "tests/two.py": "def stop():\n    return None\n",
    }
    resolver = guard._python_import_resolver(sources.get)

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="conditional global runtime import installer",
    ):
        guard._python_inventory_entries(
            "tests/test_example.py",
            test_source,
            resolver,
        )


@pytest.mark.parametrize(
    "conditional_call",
    (
        "[install_two() for _ in range(int(flag))]",
        "flag < 0 < install_two()",
    ),
)
def test_python_runtime_global_import_installers_fail_closed_in_expressions(
    conditional_call: str,
) -> None:
    test_source = (
        "import pytest\n"
        "import tests.one as helper\n"
        "def install_two():\n"
        "    global helper\n"
        "    import tests.two as helper\n"
        "    return 1\n"
        "@pytest.mark.parametrize('flag', [True, False])\n"
        "def test_case(flag):\n"
        f"    {conditional_call}\n"
        "    helper.stop()\n"
    )
    sources = {
        "tests/one.py": "def stop():\n    return None\n",
        "tests/two.py": "def stop():\n    return None\n",
    }
    resolver = guard._python_import_resolver(sources.get)

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="conditional global runtime import installer",
    ):
        guard._python_inventory_entries(
            "tests/test_example.py",
            test_source,
            resolver,
        )


def test_python_inventory_canonicalizes_transitive_import_cycles() -> None:
    test_source = (
        "from tests.first import stop\n"
        "from tests.second import continue_stop\n"
        "def test_a():\n"
        "    stop()\n"
        "def test_b():\n"
        "    continue_stop()\n"
    )

    def refs_for(
        first_value: int, second_value: int, unrelated: int
    ) -> tuple[str, ...]:
        sources = {
            "tests/first.py": (
                "from tests.second import continue_stop\n"
                f"VALUE = {first_value}\n"
                "def stop():\n"
                "    continue_stop()\n"
                "    return VALUE\n"
            ),
            "tests/second.py": (
                "from tests.first import stop\n"
                f"VALUE = {second_value}\n"
                f"UNRELATED = {unrelated}\n"
                "def continue_stop():\n"
                "    stop()\n"
                "    return VALUE\n"
            ),
        }
        resolver = guard._python_import_resolver(sources.get)
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_example.py",
                test_source,
                resolver,
            )
        )

    baseline = refs_for(1, 2, 3)
    # Ordinary helper data stays outside the posture-only test identity.
    assert baseline == refs_for(4, 2, 3)
    assert baseline == refs_for(1, 5, 3)
    assert baseline == refs_for(1, 2, 6)


def test_python_inventory_binds_transitive_cycle_runtime_abort_posture() -> None:
    test_source = "from tests.first import stop\ndef test_case():\n    stop()\n"

    def ref_for(body: str) -> str:
        sources = {
            "tests/first.py": (
                "from tests.second import continue_stop\n"
                "def stop():\n    continue_stop()\n"
            ),
            "tests/second.py": (
                f"from tests.first import stop\ndef continue_stop():\n    {body}\n"
            ),
        }
        resolver = guard._python_import_resolver(sources.get)
        return guard._python_inventory_entries(
            "tests/test_example.py",
            test_source,
            resolver,
        )[0][0].ref

    assert ref_for("return None") != ref_for("import pytest; pytest.xfail('disabled')")


def test_python_inventory_canonicalizes_star_import_dependency_cycles() -> None:
    test_source = (
        "from tests.first import stop\n"
        "from tests.second import continue_stop\n"
        "def test_a():\n"
        "    stop()\n"
        "def test_b():\n"
        "    continue_stop()\n"
    )

    def refs_for(
        first_value: int, second_value: int, unrelated: int
    ) -> tuple[str, ...]:
        sources = {
            "tests/first.py": (
                f"FIRST_VALUE = {first_value}\n"
                "def stop():\n"
                "    continue_stop()\n"
                "    return FIRST_VALUE\n"
                "from tests.second import *\n"
            ),
            "tests/second.py": (
                f"SECOND_VALUE = {second_value}\n"
                f"UNRELATED = {unrelated}\n"
                "def continue_stop():\n"
                "    stop()\n"
                "    return SECOND_VALUE\n"
                "from tests.first import *\n"
            ),
        }
        resolver = guard._python_import_resolver(sources.get)
        return tuple(
            declaration.ref
            for declaration, _source in guard._python_inventory_entries(
                "tests/test_example.py",
                test_source,
                resolver,
            )
        )

    baseline = refs_for(1, 2, 3)
    # Star-import cycles retain the same posture-only identity contract.
    assert baseline == refs_for(4, 2, 3)
    assert baseline == refs_for(1, 5, 3)
    assert baseline == refs_for(1, 2, 6)


def test_python_inventory_binds_local_helper_global_dependency() -> None:
    def ref_for(value: int) -> str:
        return guard.parse_python_declarations(
            "tests/test_example.py",
            f"VALUE = {value}\ndef prepare():\n    return VALUE\n"
            "def test_case():\n    prepare()\n",
        )[0].ref

    assert ref_for(1) != ref_for(2)


def test_python_inventory_rejects_control_flow_runtime_abort_alias() -> None:
    source = (
        "import pytest\nFLAG = False\nif FLAG:\n    stop = pytest.xfail\n"
        "else:\n    stop = lambda reason: None\n"
        "def test_case():\n    stop('disabled')\n"
    )

    with pytest.raises(guard.TestCorpusGuardError, match="runtime|abort|dynamic"):
        guard.parse_python_declarations("tests/test_example.py", source)


def test_python_inventory_ignores_discarded_functional_fixture_wrapper() -> None:
    active = guard.parse_python_declarations(
        "tests/test_example.py",
        "import pytest\ndef environment(): return None\n"
        "pytest.fixture(autouse=True)(environment)\ndef test_case(): pass\n",
    )[0].ref
    plain = guard.parse_python_declarations(
        "tests/test_example.py",
        "import pytest\ndef environment(): return None\ndef test_case(): pass\n",
    )[0].ref

    assert active == plain
