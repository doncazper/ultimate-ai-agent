from __future__ import annotations

from types import UnionType
from typing import Any, Type, Union, get_args, get_origin

from pydantic import BaseModel, ValidationError


class CapabilitySchemaError(ValueError):
    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or [message]


def is_pydantic_model(annotation: Any) -> bool:
    return isinstance(annotation, type) and issubclass(annotation, BaseModel)


def schema_for_model(model: Type[BaseModel]) -> dict[str, Any]:
    return model.model_json_schema()


def schema_from_type(annotation: Any) -> dict[str, Any]:
    if annotation is Any or annotation is None:
        return {"type": "object", "additionalProperties": True}
    if is_pydantic_model(annotation):
        return schema_for_model(annotation)
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in {Union, UnionType}:
        non_none = [arg for arg in args if arg is not type(None)]
        if len(non_none) == 1 and len(non_none) != len(args):
            schema = schema_from_type(non_none[0])
            return {"anyOf": [schema, {"type": "null"}]}
        return {"anyOf": [schema_from_type(arg) for arg in args]}
    if origin in {list, tuple, set, frozenset}:
        item_type = args[0] if args else Any
        return {"type": "array", "items": schema_from_type(item_type)}
    if origin is dict:
        return {"type": "object", "additionalProperties": True}
    if annotation is str:
        return {"type": "string"}
    if annotation is int:
        return {"type": "integer"}
    if annotation is float:
        return {"type": "number"}
    if annotation is bool:
        return {"type": "boolean"}
    if annotation is dict:
        return {"type": "object", "additionalProperties": True}
    if annotation is list:
        return {"type": "array"}
    return {"type": "object", "additionalProperties": True}


def safe_validation_error(exc: ValidationError) -> str:
    parts: list[str] = []
    for error in exc.errors():
        loc = ".".join(str(part) for part in error.get("loc", ())) or "<root>"
        parts.append(f"{loc}:{error.get('type', 'invalid')}")
    return "INPUT_VALIDATION_FAILED " + ", ".join(parts)


def validate_json_schema_instance(value: Any, schema: dict[str, Any], *, label: str = "value") -> None:
    try:
        from jsonschema import Draft202012Validator
    except Exception:
        _fallback_validate_json_schema_instance(value, schema, label=label)
        return

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.path))
    if errors:
        safe_errors = []
        for error in errors[:5]:
            path = ".".join(str(part) for part in error.path) or "<root>"
            safe_errors.append(f"{path}:{error.validator}")
        raise CapabilitySchemaError(f"{label.upper()}_VALIDATION_FAILED " + ", ".join(safe_errors), safe_errors)


def _fallback_validate_json_schema_instance(value: Any, schema: dict[str, Any], *, label: str) -> None:
    expected = schema.get("type")
    errors: list[str] = []
    if isinstance(expected, list):
        type_ok = any(_type_matches(value, item) for item in expected)
    elif isinstance(expected, str):
        type_ok = _type_matches(value, expected)
    else:
        type_ok = True
    if not type_ok:
        errors.append("<root>:type")
    if expected == "object" and isinstance(value, dict):
        required = schema.get("required", [])
        for field in required:
            if field not in value:
                errors.append(f"{field}:required")
        properties = schema.get("properties", {})
        for field, field_schema in properties.items():
            if field in value:
                try:
                    _fallback_validate_json_schema_instance(value[field], field_schema, label=field)
                except CapabilitySchemaError as exc:
                    errors.extend(f"{field}.{error}" for error in exc.errors)
        if schema.get("additionalProperties") is False:
            extras = set(value) - set(properties)
            errors.extend(f"{field}:additionalProperties" for field in sorted(extras))
    if expected == "array" and isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            try:
                _fallback_validate_json_schema_instance(item, schema["items"], label=f"{label}.{index}")
            except CapabilitySchemaError as exc:
                errors.extend(f"{index}.{error}" for error in exc.errors)
    if "enum" in schema and value not in schema["enum"]:
        errors.append("<root>:enum")
    if "const" in schema and value != schema["const"]:
        errors.append("<root>:const")
    if errors:
        raise CapabilitySchemaError(f"{label.upper()}_VALIDATION_FAILED " + ", ".join(errors[:5]), errors)


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True
