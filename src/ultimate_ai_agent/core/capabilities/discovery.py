from __future__ import annotations

import inspect
from importlib import metadata as importlib_metadata
from typing import Any

from ultimate_ai_agent.core.capabilities.models import CapabilityPack, CapabilityRegistration, CapabilitySpec


def discover_entry_points(
    registry: Any,
    *,
    group: str = "ultimate_ai_agent.capabilities",
    allow_runtime_imports: bool = False,
) -> int:
    if not allow_runtime_imports:
        return 0
    count = 0
    for entry_point in _entry_points_for_group(group):
        loaded = entry_point.load()
        result = _load_entry_point_result(loaded, registry)
        count += _register_result(registry, result)
    return count


def _entry_points_for_group(group: str):
    entry_points = importlib_metadata.entry_points()
    if hasattr(entry_points, "select"):
        return list(entry_points.select(group=group))
    return list(entry_points.get(group, ()))


def _load_entry_point_result(loaded: Any, registry: Any) -> Any:
    if isinstance(loaded, (CapabilityPack, CapabilityRegistration, CapabilitySpec, list, tuple)):
        return loaded
    if callable(loaded):
        try:
            signature = inspect.signature(loaded)
        except (TypeError, ValueError):
            return loaded()
        positional = [
            param
            for param in signature.parameters.values()
            if param.kind in {param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD}
            and param.default is param.empty
        ]
        if len(positional) == 1:
            return loaded(registry)
        return loaded()
    return loaded


def _register_result(registry: Any, result: Any) -> int:
    if result is None:
        return 0
    if isinstance(result, CapabilityPack):
        return _register_result(registry, list(result.capabilities))
    if isinstance(result, CapabilityRegistration):
        registry.register(
            result.spec,
            result.fn,
            input_model=result.input_model,
            output_model=result.output_model,
        )
        return 1
    if isinstance(result, CapabilitySpec):
        registry.register(result)
        return 1
    if isinstance(result, (list, tuple)):
        count = 0
        for item in result:
            count += _register_result(registry, item)
        return count
    raise TypeError("capability entry point must return a CapabilityPack, CapabilitySpec, registration, list, or None")
