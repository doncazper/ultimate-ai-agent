import subprocess
from pathlib import Path

import pytest

from scripts.verification import test_corpus_guard as guard


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
    assert refs[2:4] == [
        "apps/control-center/src/example.test.tsx::runs in sequence",
        "apps/control-center/src/example.test.tsx::records an expected failure",
    ]
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


@pytest.mark.parametrize("modifier", ("runIf", "skipIf"))
def test_frontend_inventory_binds_conditional_execution_modifiers(
    modifier: str,
) -> None:
    first_ref = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        f'test.{modifier}(featureEnabled)("case", () => {{}});',
    )[0].ref
    second_ref = guard.parse_frontend_declarations(
        "apps/control-center/src/example.test.tsx",
        f'test.{modifier}(!featureEnabled)("case", () => {{}});',
    )[0].ref

    assert first_ref != second_ref
    assert f"::execution-conditional:{modifier}:sha256:" in first_ref


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
        'test.skipIf(a++ + b)("case", () => {});',
    )[0].ref
    prefix_ref = guard.parse_frontend_declarations(
        path,
        'test.skipIf(a + ++b)("case", () => {});',
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

    assert [item.ref for item in declarations] == [
        "apps/control-center/src/example.spec.ts::aliased test",
        "apps/control-center/src/example.spec.ts::extended test",
    ]


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


def test_malformed_requested_base_fails_closed() -> None:
    root = Path(__file__).resolve().parents[1]
    with pytest.raises(guard.TestCorpusGuardError, match="base SHA is malformed"):
        guard.verify_test_corpus_guard(root, base_sha="not-a-sha")


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
    assert captured == [
        ["ls-tree", "-r", "--name-only", "-z", "a" * 40]
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
        "patterns = (\n"
        '                    "tests/**/test_*.py",\n'
        ")\n"
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
        "class TestCases:\n"
        "    def prepare(self, method): pass\n"
        "    setup_method = prepare\n"
        "    def test_case(self): pass\n",
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
            "if True:\n"
            '    pytest_plugins = ("tests.fixture_plugin",)\n',
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
        match="changed autouse pytest fixtures",
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

    with pytest.raises(
        guard.TestCorpusGuardError,
        match="changed module-local pytest fixture dependency",
    ):
        guard._changed_test_paths(tmp_path, "a" * 40)


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


def test_python_inventory_rejects_unresolved_dynamic_autouse_module_dependency() -> None:
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
            lambda path: (
                f"value = {enabled!r}\n" if path == "tests/target.py" else None
            )
        )
        return guard._python_module_dependency_identity(
            "tests.pkg",
            package_source,
            resolver,
        )

    assert identity_for(True) != identity_for(False)


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


def test_python_inventory_binds_post_definition_autouse_fixture_source() -> None:
    active = guard.parse_python_declarations(
        "tests/test_example.py",
        "import pytest\n"
        "def environment(): yield\n"
        "pytest.fixture(autouse=True)(environment)\n"
        "def test_case(): pass\n",
    )
    disabled = guard.parse_python_declarations(
        "tests/test_example.py",
        "import pytest\n"
        'def environment(): pytest.skip("disabled")\n'
        "pytest.fixture(autouse=True)(environment)\n"
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
            f"if {condition}:\n"
            "    from tests.fixture_plugin import shared_value\n",
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
        'pytest_plugins = ("tests.fixture_plugin",)\n'
        "def test_case(): pass\n"
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
        'pytest_plugins = ("tests.pkg.fixture_plugin",)\n'
        "def test_case(): pass\n"
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
    cache_size = len(binding_cache)

    guard._python_imported_binding_source(
        "tests.second",
        second_source,
        "SECOND",
        resolver,
    )

    assert len(binding_cache) == cache_size + 1


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
            "const load = require;\n"
            'module.exports = load("./vitest.shared.cjs");\n'
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
