from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, Type, get_type_hints

from pydantic import BaseModel

from ultimate_ai_agent.core.capabilities.models import CapabilityPolicy, CapabilityRegistration, CapabilitySpec
from ultimate_ai_agent.core.capabilities.schemas import is_pydantic_model, schema_for_model, schema_from_type


def capability(
    *,
    name: str,
    title: str,
    description: str,
    version: str = "1.0.0",
    capability_id: str | None = None,
    input_schema: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
    input_model: Type[BaseModel] | None = None,
    output_model: Type[BaseModel] | None = None,
    tags: set[str] | None = None,
    policy: CapabilityPolicy | None = None,
    source: str = "python",
    metadata: dict[str, Any] | None = None,
    instructions: str | None = None,
    examples: list[dict[str, Any]] | None = None,
    registry: Any | None = None,
    replace: bool = False,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorate(fn: Callable[..., Any]) -> Callable[..., Any]:
        inferred_input_model = input_model or _infer_input_model(fn)
        inferred_output_model = output_model or _infer_output_model(fn)
        spec = CapabilitySpec(
            id=capability_id or f"capability:{name}:{version}",
            name=name,
            version=version,
            title=title,
            description=description,
            tags=tags or set(),
            input_schema=input_schema or _input_schema(fn, inferred_input_model),
            output_schema=output_schema or _output_schema(fn, inferred_output_model),
            policy=policy or CapabilityPolicy(),
            source=source,
            metadata=metadata or {},
            callable_ref=f"{fn.__module__}.{fn.__qualname__}",
            instructions=instructions,
            examples=examples or [],
        )
        setattr(fn, "__capability_spec__", spec)
        setattr(fn, "__capability_input_model__", inferred_input_model)
        setattr(fn, "__capability_output_model__", inferred_output_model)
        if registry is not None:
            registry.register(
                spec,
                fn,
                replace=replace,
                input_model=inferred_input_model,
                output_model=inferred_output_model,
            )

        @wraps(fn)
        def passthrough(*args: Any, **kwargs: Any) -> Any:
            return fn(*args, **kwargs)

        setattr(passthrough, "__capability_spec__", spec)
        setattr(passthrough, "__capability_input_model__", inferred_input_model)
        setattr(passthrough, "__capability_output_model__", inferred_output_model)
        return passthrough

    return decorate


def tool_capability(**kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    return capability(**kwargs)


def get_capability_spec(fn: Callable[..., Any]) -> CapabilitySpec:
    spec = getattr(fn, "__capability_spec__", None)
    if not isinstance(spec, CapabilitySpec):
        raise ValueError("function is not decorated with @capability")
    return spec


def as_registration(fn: Callable[..., Any]) -> CapabilityRegistration:
    return CapabilityRegistration(
        spec=get_capability_spec(fn),
        fn=fn,
        input_model=getattr(fn, "__capability_input_model__", None),
        output_model=getattr(fn, "__capability_output_model__", None),
    )


def _infer_input_model(fn: Callable[..., Any]) -> Type[BaseModel] | None:
    hints = _safe_type_hints(fn)
    parameters = list(inspect.signature(fn).parameters.values())
    candidates = []
    if len(parameters) >= 2:
        candidates.append(parameters[1].name)
    if len(parameters) == 1:
        candidates.append(parameters[0].name)
    candidates.extend(param.name for param in parameters if param.name in {"args", "arguments", "input"})
    for name in candidates:
        annotation = hints.get(name)
        if is_pydantic_model(annotation):
            return annotation
    return None


def _infer_output_model(fn: Callable[..., Any]) -> Type[BaseModel] | None:
    annotation = _safe_type_hints(fn).get("return")
    if is_pydantic_model(annotation):
        return annotation
    return None


def _input_schema(fn: Callable[..., Any], input_model: Type[BaseModel] | None) -> dict[str, Any]:
    if input_model is not None:
        return schema_for_model(input_model)
    parameters = list(inspect.signature(fn).parameters.values())
    if len(parameters) == 1:
        annotation = _safe_type_hints(fn).get(parameters[0].name, Any)
        return schema_from_type(annotation)
    if len(parameters) >= 2:
        annotation = _safe_type_hints(fn).get(parameters[1].name, Any)
        return schema_from_type(annotation)
    return {"type": "object", "additionalProperties": True}


def _output_schema(fn: Callable[..., Any], output_model: Type[BaseModel] | None) -> dict[str, Any] | None:
    if output_model is not None:
        return schema_for_model(output_model)
    annotation = _safe_type_hints(fn).get("return")
    if annotation is None or annotation is inspect.Signature.empty:
        return None
    schema = schema_from_type(annotation)
    return schema if schema != {"type": "object", "additionalProperties": True} else None


def _safe_type_hints(fn: Callable[..., Any]) -> dict[str, Any]:
    try:
        return get_type_hints(fn)
    except Exception:
        return getattr(fn, "__annotations__", {})
