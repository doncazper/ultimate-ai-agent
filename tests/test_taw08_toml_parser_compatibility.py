from __future__ import annotations

import builtins
import importlib
import runpy
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import pytest

from scripts import verify_tool_aware_cognition_taw08 as verifier


SOURCE = Path(verifier.__file__)


def _selection(importer) -> dict[str, object]:
    original_import = builtins.__import__

    def select_parser(name, *args, **kwargs):
        if name in ("tomllib", "tomli"):
            return importer(name, *args, **kwargs)
        return original_import(name, *args, **kwargs)

    # The verifier prepends its repository paths during import; isolate those
    # additions as well as the parser hook, including on import failure.
    with (
        patch.object(sys, "path", list(sys.path)),
        patch("builtins.__import__", select_parser),
    ):
        return runpy.run_path(str(SOURCE))


def test_stdlib_selection_preserves_module_identity_without_backport_import() -> None:
    stdlib = ModuleType("tomllib")
    calls: list[str] = []

    def importer(name, *_args):
        calls.append(name)
        assert name == "tomllib"
        return stdlib

    selected = _selection(importer)
    assert calls == ["tomllib"]
    assert selected["tomllib"] is stdlib
    assert selected["_stdlib_toml"] is stdlib
    assert "_backport_toml" not in selected


def test_missing_stdlib_selects_backport_once_with_the_same_module_identity() -> None:
    backport = ModuleType("tomli")
    calls: list[str] = []

    def importer(name, *_args):
        calls.append(name)
        if name == "tomllib":
            raise ModuleNotFoundError("stdlib parser unavailable")
        assert name == "tomli"
        return backport

    selected = _selection(importer)
    assert calls == ["tomllib", "tomli"]
    assert selected["tomllib"] is backport
    assert selected["_backport_toml"] is backport
    assert "_stdlib_toml" not in selected


@pytest.mark.parametrize("failure_kind", ("import", "runtime"))
def test_non_missing_stdlib_errors_propagate_without_fallback(
    failure_kind: str,
) -> None:
    failure = (
        ImportError("parser import failed")
        if failure_kind == "import"
        else RuntimeError("parser failed")
    )
    calls: list[str] = []

    def importer(name, *_args):
        calls.append(name)
        raise failure

    with pytest.raises(type(failure)) as caught:
        _selection(importer)
    assert caught.value is failure
    assert calls == ["tomllib"]


@pytest.mark.parametrize("failure_kind", ("missing", "import", "runtime"))
def test_backport_import_errors_propagate_unchanged(failure_kind: str) -> None:
    failures = {
        "missing": ModuleNotFoundError("backport unavailable"),
        "import": ImportError("backport import failed"),
        "runtime": RuntimeError("backport failed"),
    }
    failure = failures[failure_kind]
    calls: list[str] = []

    def importer(name, *_args):
        calls.append(name)
        if name == "tomllib":
            raise ModuleNotFoundError("stdlib parser unavailable")
        raise failure

    with pytest.raises(type(failure)) as caught:
        _selection(importer)
    assert caught.value is failure
    assert calls == ["tomllib", "tomli"]


def test_actual_interpreter_selects_the_original_parser_and_error_class() -> None:
    expected = importlib.import_module(
        "tomllib" if sys.version_info >= (3, 11) else "tomli"
    )
    assert verifier.tomllib is expected
    assert verifier.tomllib.loads is expected.loads
    assert verifier.tomllib.TOMLDecodeError is expected.TOMLDecodeError
    assert verifier.tomllib.loads("[project]\nname = 'sample'\n") == {
        "project": {"name": "sample"}
    }
    with pytest.raises(expected.TOMLDecodeError):
        verifier.tomllib.loads("[unterminated")


@pytest.mark.parametrize(
    "owner", ("verify_locked_evaluator_environment", "_materialize_locked_environment")
)
@pytest.mark.parametrize("substitution", ("public-alias", "module-attributes"))
def test_both_consumers_observe_parser_and_error_substitution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, owner: str, substitution: str
) -> None:
    class SelectedParserError(ValueError):
        pass

    failure = SelectedParserError("synthetic parser failure")

    def loads(_text: str):
        raise failure

    if substitution == "public-alias":
        monkeypatch.setattr(
            verifier,
            "tomllib",
            SimpleNamespace(loads=loads, TOMLDecodeError=SelectedParserError),
        )
    else:
        monkeypatch.setattr(verifier.tomllib, "loads", loads)
        monkeypatch.setattr(verifier.tomllib, "TOMLDecodeError", SelectedParserError)
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "pyproject.toml").write_bytes(b"version = 1\n")
    (candidate / "uv.lock").write_bytes(b"version = 1\n")
    environment = tmp_path / "environment"
    environment.mkdir()
    (environment / "pyvenv.cfg").write_text(
        "include-system-site-packages = false\n", encoding="utf-8"
    )
    monkeypatch.setenv(verifier._ENVIRONMENT_ROOT_ENV, str(environment))

    with pytest.raises(RuntimeError, match="metadata is invalid") as caught:
        if owner == "verify_locked_evaluator_environment":
            verifier.verify_locked_evaluator_environment(
                repository_root=candidate,
                locked_content_by_path_ref={
                    "repo-path-ref:pyproject.toml": b"version = 1\n",
                    "repo-path-ref:uv.lock": b"version = 1\n",
                },
            )
        else:
            verifier._materialize_locked_environment(
                candidate_root=candidate,
                environment_root=environment,
                provisioned_wheelhouse=tmp_path / "provisioned",
                selected_wheelhouse=tmp_path / "selected",
            )
    assert caught.value.__cause__ is failure
    assert not (tmp_path / "selected").exists()
