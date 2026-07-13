from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "packaging" / "sealed-calculation" / "runner.py"


def _load_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "uaa_sealed_calculation_runner", RUNNER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = _load_runner()


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("2 + 3 * 4", "14"),
        ("(10 - 4) / 3", "2"),
        ("2 ** 10", "1024"),
        ("7 // 2 + 7 % 2", "4"),
        ("-2.5e2 + 10", "-240"),
        ("9999999999999999 + 1", "10000000000000000"),
        ("10 ** 99 + 1", "1" + "0" * 98 + "1"),
        ("0.123456789012345678901", "0.123456789012345678901"),
        ("-7 // 2", "-4"),
        ("-7 % 2", "1"),
    ],
)
def test_runner_returns_canonical_bounded_numeric_evidence(
    expression: str,
    expected: str,
) -> None:
    response, return_code = RUNNER._process(
        json.dumps({"expression": expression}).encode("utf-8")
    )

    assert return_code == 0
    assert response["status"] == "succeeded"
    assert response["result"] == expected
    assert len(response["expression_sha256"]) == 64
    assert len(response["output_sha256"]) == 64


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os')",
        "open('/tmp/item')",
        "value",
        "'text'",
        "[1, 2]",
        "(1).__class__",
        "1 if 1 else 0",
        "1 << 2",
        "10 / 0",
        "1 / 3",
        "2 ** 1001",
        "1e101",
        "(" * 25 + "1" + ")" * 25,
        "+".join("1" for _ in range(60)),
    ],
)
def test_runner_fails_closed_for_code_and_resource_abuse(expression: str) -> None:
    response, return_code = RUNNER._process(
        json.dumps({"expression": expression}).encode("utf-8")
    )

    assert return_code != 0
    assert response["status"] == "denied"
    assert str(response["reason_code"]).isupper()
    assert "expression" not in response
    assert "result" not in response


def test_runner_rejects_oversized_and_malformed_request_shapes() -> None:
    oversized, oversized_code = RUNNER._process(
        json.dumps({"expression": "1" * 513}).encode("utf-8")
    )
    malformed, malformed_code = RUNNER._process(
        json.dumps({"expression": "1 + 1", "authority": True}).encode("utf-8")
    )

    assert oversized_code != 0
    assert oversized["reason_code"] == "EXPRESSION_SIZE_LIMIT_EXCEEDED"
    assert malformed_code != 0
    assert malformed["reason_code"] == "REQUEST_SHAPE_DENIED"
