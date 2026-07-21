"""Repository JSON Schema extensions for prompt-module manifests."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from jsonschema import Draft202012Validator, ValidationError, validators


def _validate_unique_by(
    validator: Draft202012Validator,
    property_name: str,
    instance: Any,
    schema: dict[str, Any],
) -> Iterator[ValidationError]:
    del validator, schema
    if not isinstance(instance, list) or not isinstance(property_name, str):
        return
    seen: set[str] = set()
    for item in instance:
        if not isinstance(item, dict):
            continue
        value = item.get(property_name)
        if not isinstance(value, str):
            continue
        if value in seen:
            yield ValidationError(
                "array items must use unique property references"
            )
            return
        seen.add(value)


PromptModuleManifestSchemaValidator = validators.extend(
    Draft202012Validator,
    {"x-uaa-uniqueBy": _validate_unique_by},
)


def prompt_module_manifest_schema_errors(
    schema: dict[str, Any],
    manifest: dict[str, Any],
) -> tuple[ValidationError, ...]:
    """Return deterministic schema errors, including UAA uniqueness rules."""

    validator = PromptModuleManifestSchemaValidator(schema)
    return tuple(
        sorted(
            validator.iter_errors(manifest),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
    )


__all__ = [
    "PromptModuleManifestSchemaValidator",
    "prompt_module_manifest_schema_errors",
]
