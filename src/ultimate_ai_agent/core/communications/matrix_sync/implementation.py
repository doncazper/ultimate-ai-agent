from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from types import CodeType


def matrix_sync_implementation_ref(
    implementation: Callable[..., object],
) -> str:
    target = getattr(implementation, "__func__", implementation)
    code = getattr(target, "__code__", None)
    if code is None:
        raise ValueError("MATRIX_SYNC_IMPLEMENTATION_IDENTITY_REQUIRED")
    payload = {
        "code_sha256": _matrix_sync_code_sha256(code),
        "module": str(getattr(target, "__module__", "")),
        "qualname": str(getattr(target, "__qualname__", "")),
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return (
        f"implementation-ref:matrix-sync:sha256:{hashlib.sha256(encoded).hexdigest()}"
    )


def _matrix_sync_code_sha256(code: CodeType) -> str:
    payload = {
        "argcount": code.co_argcount,
        "cellvars": code.co_cellvars,
        "code_sha256": hashlib.sha256(code.co_code).hexdigest(),
        "constants": [_constant_identity(item) for item in code.co_consts],
        "flags": code.co_flags,
        "freevars": code.co_freevars,
        "kwonlyargcount": code.co_kwonlyargcount,
        "name": code.co_name,
        "names": code.co_names,
        "posonlyargcount": code.co_posonlyargcount,
        "qualname": code.co_qualname,
        "varnames": code.co_varnames,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _constant_identity(value: object) -> object:
    if isinstance(value, CodeType):
        return {"code_sha256": _matrix_sync_code_sha256(value)}
    if isinstance(value, bytes):
        return {"bytes_sha256": hashlib.sha256(value).hexdigest()}
    if isinstance(value, str):
        return {"string_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest()}
    if isinstance(value, tuple):
        return [_constant_identity(item) for item in value]
    if isinstance(value, frozenset):
        values = [_constant_identity(item) for item in value]
        return sorted(
            values,
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )
    if value is Ellipsis:
        return {"literal": "ellipsis"}
    if value is None or isinstance(value, (bool, int, float, complex)):
        return {"literal_type": type(value).__name__, "value": repr(value)}
    raise ValueError("MATRIX_SYNC_IMPLEMENTATION_CONSTANT_UNSUPPORTED")
