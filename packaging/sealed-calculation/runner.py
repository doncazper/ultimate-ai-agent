from __future__ import annotations

import ast
import hashlib
import json
import resource
import re
import sys
from decimal import (
    Context,
    Decimal,
    DecimalException,
    DivisionByZero,
    Inexact,
    InvalidOperation,
    Rounded,
    localcontext,
)
from typing import Final


SCHEMA_VERSION: Final = "uaa-sealed-calculation-runner.v1"
MAX_INPUT_BYTES: Final = 1024
MAX_EXPRESSION_BYTES: Final = 512
MAX_AST_NODES: Final = 96
MAX_AST_DEPTH: Final = 20
MAX_ABSOLUTE_VALUE: Final = Decimal("1e100")
MAX_EXPONENT: Final = 1000
MAX_OUTPUT_BYTES: Final = 1024
RUNNER_CONTRACT_REF: Final = "runner-contract-ref:sealed-calculation-ast-v1"
GRAMMAR_POLICY_REF: Final = "grammar-policy-ref:sealed-arithmetic-v1"
ALLOWED_EXPRESSION_BYTES: Final = frozenset(b"0123456789.eE+-*/%() \t\r\n")
DECIMAL_CONTEXT: Final = Context(prec=110, Emin=-200, Emax=200)
DECIMAL_CONTEXT.traps[Inexact] = True
DECIMAL_CONTEXT.traps[Rounded] = True
NUMBER_TOKEN_RE: Final = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z")


class CalculationDenied(ValueError):
    pass


def _bounded_number(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise CalculationDenied("NON_NUMERIC_VALUE_DENIED")
    try:
        number = value if isinstance(value, Decimal) else Decimal(str(value))
    except InvalidOperation as exc:
        raise CalculationDenied("NON_NUMERIC_VALUE_DENIED") from exc
    if not number.is_finite():
        raise CalculationDenied("NON_FINITE_VALUE_DENIED")
    if abs(number) > MAX_ABSOLUTE_VALUE:
        raise CalculationDenied("NUMERIC_MAGNITUDE_LIMIT_EXCEEDED")
    return number


def _pow(left: Decimal, right: Decimal) -> Decimal:
    if right != right.to_integral_value() or abs(right) > MAX_EXPONENT:
        raise CalculationDenied("EXPONENT_LIMIT_EXCEEDED")
    try:
        with localcontext(DECIMAL_CONTEXT) as context:
            return _bounded_number(context.power(left, int(right)))
    except DecimalException as exc:
        raise CalculationDenied("POWER_OPERATION_DENIED") from exc


def _evaluate(node: ast.AST, expression: str, *, depth: int = 0) -> Decimal:
    if depth > MAX_AST_DEPTH:
        raise CalculationDenied("EXPRESSION_DEPTH_LIMIT_EXCEEDED")
    if isinstance(node, ast.Expression):
        return _evaluate(node.body, expression, depth=depth + 1)
    if isinstance(node, ast.Constant):
        token = ast.get_source_segment(expression, node)
        if token is None or NUMBER_TOKEN_RE.fullmatch(token) is None:
            raise CalculationDenied("NUMBER_LITERAL_DENIED")
        try:
            return _bounded_number(Decimal(token))
        except InvalidOperation as exc:
            raise CalculationDenied("NUMBER_LITERAL_DENIED") from exc
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _evaluate(node.operand, expression, depth=depth + 1)
        return _bounded_number(value if isinstance(node.op, ast.UAdd) else -value)
    if isinstance(node, ast.BinOp):
        left = _evaluate(node.left, expression, depth=depth + 1)
        right = _evaluate(node.right, expression, depth=depth + 1)
        try:
            with localcontext(DECIMAL_CONTEXT):
                if isinstance(node.op, ast.Add):
                    return _bounded_number(left + right)
                if isinstance(node.op, ast.Sub):
                    return _bounded_number(left - right)
                if isinstance(node.op, ast.Mult):
                    return _bounded_number(left * right)
                if isinstance(node.op, ast.Div):
                    return _bounded_number(left / right)
                if isinstance(node.op, ast.FloorDiv):
                    quotient = left // right
                    remainder = left % right
                    if remainder and (left < 0) != (right < 0):
                        quotient -= 1
                    return _bounded_number(quotient)
                if isinstance(node.op, ast.Mod):
                    quotient = left // right
                    remainder = left % right
                    if remainder and (left < 0) != (right < 0):
                        quotient -= 1
                    return _bounded_number(left - quotient * right)
                if isinstance(node.op, ast.Pow):
                    return _pow(left, right)
        except (DivisionByZero, ZeroDivisionError) as exc:
            raise CalculationDenied("DIVISION_BY_ZERO_DENIED") from exc
        except DecimalException as exc:
            reason = (
                "INEXACT_RESULT_DENIED"
                if isinstance(exc, (Inexact, Rounded))
                else "NUMERIC_OPERATION_DENIED"
            )
            raise CalculationDenied(reason) from exc
        raise CalculationDenied("OPERATOR_NOT_ALLOWLISTED")
    raise CalculationDenied("SYNTAX_NOT_ALLOWLISTED")


def _deny(reason_code: str) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "denied",
        "reason_code": reason_code,
        "safe_summary": "Sealed calculation input was denied by the bounded interpreter.",
    }


def _format_result(value: Decimal) -> str:
    if value.is_zero():
        return "0"
    normalized = value.normalize(context=DECIMAL_CONTEXT)
    result = format(normalized, "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    if len(result.encode("ascii")) > 128:
        raise CalculationDenied("RESULT_SIZE_LIMIT_EXCEEDED")
    return result


def _validate_parenthesis_depth(expression: str) -> None:
    depth = 0
    for character in expression:
        if character == "(":
            depth += 1
            if depth > MAX_AST_DEPTH:
                raise CalculationDenied("EXPRESSION_DEPTH_LIMIT_EXCEEDED")
        elif character == ")":
            depth -= 1
            if depth < 0:
                raise CalculationDenied("EXPRESSION_PARSE_DENIED")
    if depth != 0:
        raise CalculationDenied("EXPRESSION_PARSE_DENIED")


def _process(raw: bytes) -> tuple[dict[str, object], int]:
    try:
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict) or set(payload) != {"expression"}:
            raise CalculationDenied("REQUEST_SHAPE_DENIED")
        expression = payload["expression"]
        if not isinstance(expression, str):
            raise CalculationDenied("EXPRESSION_TEXT_REQUIRED")
        encoded_expression = expression.encode("utf-8")
        if not encoded_expression or len(encoded_expression) > MAX_EXPRESSION_BYTES:
            raise CalculationDenied("EXPRESSION_SIZE_LIMIT_EXCEEDED")
        if any(value not in ALLOWED_EXPRESSION_BYTES for value in encoded_expression):
            raise CalculationDenied("EXPRESSION_CHARACTER_NOT_ALLOWLISTED")
        _validate_parenthesis_depth(expression)
        tree = ast.parse(expression, mode="eval")
        if sum(1 for _ in ast.walk(tree)) > MAX_AST_NODES:
            raise CalculationDenied("EXPRESSION_NODE_LIMIT_EXCEEDED")
        result = _evaluate(tree, expression)
        result_text = _format_result(result)
        output_sha256 = hashlib.sha256(result_text.encode("ascii")).hexdigest()
        response = {
            "schema_version": SCHEMA_VERSION,
            "status": "succeeded",
            "expression_sha256": hashlib.sha256(encoded_expression).hexdigest(),
            "output_sha256": output_sha256,
            "result": result_text,
            "safe_summary": "Sealed deterministic calculation completed.",
        }
        return response, 0
    except (CalculationDenied, SyntaxError, UnicodeError, json.JSONDecodeError) as exc:
        reason = (
            str(exc)
            if isinstance(exc, CalculationDenied)
            else "EXPRESSION_PARSE_DENIED"
        )
        return _deny(reason), 2
    except Exception:
        return _deny("CALCULATION_FAILED_CLOSED"), 3


def main() -> int:
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
    resource.setrlimit(resource.RLIMIT_AS, (64 * 1024 * 1024, 64 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
    resource.setrlimit(resource.RLIMIT_NPROC, (1, 1))
    resource.setrlimit(resource.RLIMIT_STACK, (8 * 1024 * 1024, 8 * 1024 * 1024))
    print(
        json.dumps(
            {
                "frame": "ready",
                "grammar_policy_ref": GRAMMAR_POLICY_REF,
                "protocol": SCHEMA_VERSION,
                "runner_contract_ref": RUNNER_CONTRACT_REF,
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        file=sys.stderr,
        flush=True,
    )
    raw = sys.stdin.buffer.readline(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES or sys.stdin.buffer.read(1):
        response, return_code = _deny("REQUEST_SIZE_LIMIT_EXCEEDED"), 2
    else:
        try:
            request_payload = json.loads(raw.decode("utf-8"))
            expression = (
                request_payload.get("expression")
                if isinstance(request_payload, dict)
                else None
            )
            expression_sha256 = (
                hashlib.sha256(expression.encode("utf-8")).hexdigest()
                if isinstance(expression, str)
                else "invalid"
            )
        except (UnicodeError, json.JSONDecodeError):
            expression_sha256 = "invalid"
        print(
            json.dumps(
                {
                    "expression_sha256": expression_sha256,
                    "frame": "input_accepted",
                    "protocol": SCHEMA_VERSION,
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=sys.stderr,
            flush=True,
        )
        response, return_code = _process(raw)
    encoded = json.dumps(response, sort_keys=True, separators=(",", ":")).encode(
        "ascii"
    )
    if len(encoded) > MAX_OUTPUT_BYTES:
        encoded = json.dumps(
            _deny("OUTPUT_SIZE_LIMIT_EXCEEDED"), sort_keys=True
        ).encode("ascii")
        return_code = 3
    sys.stdout.buffer.write(encoded + b"\n")
    sys.stdout.buffer.flush()
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
