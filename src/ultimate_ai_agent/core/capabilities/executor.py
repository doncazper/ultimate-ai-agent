from __future__ import annotations

import asyncio
import inspect
import time
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, ValidationError

from ultimate_ai_agent.core.capabilities.models import CapabilityRegistration, CapabilityResult, CapabilitySpec
from ultimate_ai_agent.core.capabilities.observability import CapabilityEvent, CapabilityEventSink, NoopCapabilityEventSink
from ultimate_ai_agent.core.capabilities.policy import can_retry, normalize_run_context, policy_denial_reasons
from ultimate_ai_agent.core.capabilities.schemas import (
    CapabilitySchemaError,
    safe_validation_error,
    validate_json_schema_instance,
)
from ultimate_ai_agent.core.observability import build_safe_ref, classify_duration, record_session_event


ApprovalCallback = Callable[[CapabilitySpec, dict[str, Any], Any], bool | Awaitable[bool] | Any]


class CapabilityExecutor:
    def __init__(
        self,
        *,
        approval_callback: ApprovalCallback | None = None,
        event_sink: CapabilityEventSink | None = None,
    ):
        self.approval_callback = approval_callback
        self.event_sink = event_sink or NoopCapabilityEventSink()

    async def execute(
        self,
        registration: CapabilityRegistration | None,
        capability_name: str,
        arguments: Any,
        run_context: Any,
    ) -> CapabilityResult:
        if registration is None:
            return CapabilityResult.failure(
                capability_name,
                error="CAPABILITY_NOT_FOUND",
                metadata={"error_code": "CAPABILITY_NOT_FOUND"},
            )
        spec = registration.spec
        context = normalize_run_context(run_context)
        denials = policy_denial_reasons(spec, context.agent_name, context.user_scopes)
        if denials:
            self.event_sink.emit(
                CapabilityEvent(
                    "capability.call.denied",
                    capability_name=spec.name,
                    agent_name=context.agent_name,
                    status="denied",
                    metadata={"reason_codes": denials},
                )
            )
            _record_capability_session_event(
                "capability.execution.denied",
                capability_name=spec.name,
                agent_name=context.agent_name,
                run_id=_run_id_from_context(context),
                status="denied",
                lifecycle_state="denied",
                reason_codes=denials,
            )
            return CapabilityResult.failure(spec.name, error=";".join(denials), metadata={"reason_codes": denials})

        try:
            validated_arguments = self._validate_arguments(registration, arguments)
        except CapabilitySchemaError as exc:
            return CapabilityResult.failure(
                spec.name,
                error=str(exc),
                metadata={"error_code": "INPUT_VALIDATION_FAILED", "validation_errors": exc.errors},
            )
        except ValidationError as exc:
            return CapabilityResult.failure(
                spec.name,
                error=safe_validation_error(exc),
                metadata={"error_code": "INPUT_VALIDATION_FAILED"},
            )

        if spec.policy.requires_approval:
            self.event_sink.emit(
                CapabilityEvent(
                    "capability.call.approval_required",
                    capability_name=spec.name,
                    agent_name=context.agent_name,
                    status="approval_required",
                    metadata={"risk": spec.policy.risk.value},
                )
            )
            approved = await self._approved(spec, _safe_argument_preview(arguments), run_context)
            if not approved:
                self.event_sink.emit(
                    CapabilityEvent(
                        "capability.call.denied",
                        capability_name=spec.name,
                        agent_name=context.agent_name,
                        status="denied",
                        metadata={"reason_codes": ["APPROVAL_REQUIRED"]},
                    )
                )
                _record_capability_session_event(
                    "capability.execution.denied",
                    capability_name=spec.name,
                    agent_name=context.agent_name,
                    run_id=_run_id_from_context(context),
                    status="denied",
                    lifecycle_state="waiting_approval",
                    reason_codes=["APPROVAL_REQUIRED"],
                    error_code="APPROVAL_REQUIRED",
                )
                return CapabilityResult.failure(
                    spec.name,
                    error="APPROVAL_REQUIRED",
                    metadata={"error_code": "APPROVAL_REQUIRED"},
                )

        if registration.fn is None:
            return CapabilityResult.failure(
                spec.name,
                error="CAPABILITY_NOT_EXECUTABLE",
                metadata={"error_code": "CAPABILITY_NOT_EXECUTABLE"},
            )

        attempts = 1 + (spec.policy.max_retries if can_retry(spec) else 0)
        last_error: str | None = None
        for attempt in range(1, attempts + 1):
            start = time.perf_counter()
            self.event_sink.emit(
                CapabilityEvent(
                    "capability.call.started",
                    capability_name=spec.name,
                    agent_name=context.agent_name,
                    status="started",
                    metadata={"attempt": attempt, "argument_keys": _argument_keys(arguments)},
                )
            )
            _record_capability_session_event(
                "capability.execution.started",
                capability_name=spec.name,
                agent_name=context.agent_name,
                run_id=_run_id_from_context(context),
                status="started",
                lifecycle_state="started",
                reason_codes=["CAPABILITY_EXECUTION_STARTED"],
                metadata={"attempt": attempt, "argument_count": len(_argument_keys(arguments))},
            )
            try:
                raw = await asyncio.wait_for(
                    self._call_once(registration.fn, run_context, validated_arguments),
                    timeout=spec.policy.timeout_s,
                )
                result = self._coerce_result(spec, registration, raw)
                duration_ms = (time.perf_counter() - start) * 1000
                self.event_sink.emit(
                    CapabilityEvent(
                        "capability.call.succeeded",
                        capability_name=spec.name,
                        agent_name=context.agent_name,
                        status="succeeded",
                        duration_ms=duration_ms,
                        metadata={"attempt": attempt},
                    )
                )
                _record_capability_session_event(
                    "capability.execution.succeeded",
                    capability_name=spec.name,
                    agent_name=context.agent_name,
                    run_id=_run_id_from_context(context),
                    status="succeeded",
                    lifecycle_state=classify_duration(duration_ms),
                    duration_ms=duration_ms,
                    reason_codes=["CAPABILITY_EXECUTION_SUCCEEDED"],
                    metadata={"attempt": attempt},
                )
                return result.model_copy(
                    update={
                        "metadata": {
                            **result.metadata,
                            "duration_ms": duration_ms,
                            "attempts": attempt,
                        }
                    }
                )
            except (CapabilitySchemaError, ValidationError) as exc:
                duration_ms = (time.perf_counter() - start) * 1000
                self.event_sink.emit(
                    CapabilityEvent(
                        "capability.call.output_validation_failed",
                        capability_name=spec.name,
                        agent_name=context.agent_name,
                        status="failed",
                        duration_ms=duration_ms,
                        error_class=type(exc).__name__,
                    )
                )
                _record_capability_session_event(
                    "capability.execution.failed",
                    capability_name=spec.name,
                    agent_name=context.agent_name,
                    run_id=_run_id_from_context(context),
                    status="failed",
                    lifecycle_state="failed",
                    duration_ms=duration_ms,
                    reason_codes=["OUTPUT_VALIDATION_FAILED"],
                    error_code=type(exc).__name__,
                    error_summary="Capability output validation failed safely.",
                    metadata={"attempt": attempt},
                )
                return CapabilityResult.failure(
                    spec.name,
                    error="OUTPUT_VALIDATION_FAILED",
                    metadata={"error_code": "OUTPUT_VALIDATION_FAILED", "attempts": attempt},
                )
            except asyncio.TimeoutError:
                last_error = "CAPABILITY_TIMEOUT"
                self._emit_failed(spec.name, context.agent_name, start, "TimeoutError", attempt)
                _record_capability_session_event(
                    "capability.execution.timeout",
                    capability_name=spec.name,
                    agent_name=context.agent_name,
                    run_id=_run_id_from_context(context),
                    status="timeout",
                    lifecycle_state="timeout",
                    duration_ms=(time.perf_counter() - start) * 1000,
                    reason_codes=["CAPABILITY_TIMEOUT"],
                    error_code="TimeoutError",
                    error_summary="Capability execution timed out safely.",
                    metadata={"attempt": attempt},
                )
            except Exception as exc:
                last_error = _safe_exception_message(exc)
                self._emit_failed(spec.name, context.agent_name, start, type(exc).__name__, attempt)
                _record_capability_session_event(
                    "capability.execution.failed",
                    capability_name=spec.name,
                    agent_name=context.agent_name,
                    run_id=_run_id_from_context(context),
                    status="failed",
                    lifecycle_state="failed",
                    duration_ms=(time.perf_counter() - start) * 1000,
                    reason_codes=["CAPABILITY_HANDLER_FAILED"],
                    error_code=type(exc).__name__,
                    error_summary="Capability execution failed safely.",
                    metadata={"attempt": attempt},
                )

        return CapabilityResult.failure(
            spec.name,
            error=last_error or "CAPABILITY_FAILED",
            metadata={"error_code": last_error or "CAPABILITY_FAILED", "attempts": attempts},
        )

    def _validate_arguments(self, registration: CapabilityRegistration, arguments: Any) -> Any:
        raw_arguments = {} if arguments is None else arguments
        schema_value = raw_arguments.model_dump(mode="json") if isinstance(raw_arguments, BaseModel) else raw_arguments
        validate_json_schema_instance(schema_value, registration.spec.input_schema, label="input")
        if registration.input_model is not None:
            return registration.input_model.model_validate(raw_arguments)
        return raw_arguments

    async def _approved(self, spec: CapabilitySpec, safe_arguments: dict[str, Any], run_context: Any) -> bool:
        if self.approval_callback is None:
            return False
        decision = self.approval_callback(spec, safe_arguments, run_context)
        if inspect.isawaitable(decision):
            decision = await decision
        if isinstance(decision, bool):
            return decision
        return bool(getattr(decision, "allowed", False))

    async def _call_once(self, fn: Callable[..., Any], run_context: Any, arguments: Any) -> Any:
        if inspect.iscoroutinefunction(fn):
            return await _invoke_callable(fn, run_context, arguments)
        result = await asyncio.to_thread(_invoke_sync_callable, fn, run_context, arguments)
        if inspect.isawaitable(result):
            return await result
        return result

    def _coerce_result(self, spec: CapabilitySpec, registration: CapabilityRegistration, raw: Any) -> CapabilityResult:
        if isinstance(raw, CapabilityResult):
            result = raw if raw.capability_name == spec.name else raw.model_copy(update={"capability_name": spec.name})
        else:
            raw = _validate_output_model(registration, raw)
            if isinstance(raw, BaseModel):
                structured = raw.model_dump(mode="json")
                result = CapabilityResult.success(spec.name, structured_content=structured)
            elif isinstance(raw, str):
                result = CapabilityResult.success(spec.name, content=raw)
            elif raw is None:
                result = CapabilityResult.success(spec.name)
            else:
                result = CapabilityResult.success(spec.name, structured_content=raw)
        if spec.output_schema is not None:
            output_value = result.structured_content if result.structured_content is not None else result.content
            validate_json_schema_instance(output_value, spec.output_schema, label="output")
        if spec.policy.redact_output:
            return result.model_copy(update={"content": None, "structured_content": None, "metadata": {**result.metadata, "redacted": True}})
        return result

    def _emit_failed(self, capability_name: str, agent_name: str, start: float, error_class: str, attempt: int) -> None:
        self.event_sink.emit(
            CapabilityEvent(
                "capability.call.failed",
                capability_name=capability_name,
                agent_name=agent_name,
                status="failed",
                duration_ms=(time.perf_counter() - start) * 1000,
                error_class=error_class,
                metadata={"attempt": attempt},
            )
        )


async def _invoke_callable(fn: Callable[..., Any], run_context: Any, arguments: Any) -> Any:
    result = _invoke_sync_callable(fn, run_context, arguments)
    if inspect.isawaitable(result):
        return await result
    return result


def _invoke_sync_callable(fn: Callable[..., Any], run_context: Any, arguments: Any) -> Any:
    signature = inspect.signature(fn)
    positional = [
        param
        for param in signature.parameters.values()
        if param.kind in {param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD}
    ]
    if not positional:
        return fn()
    if len(positional) == 1:
        return fn(arguments)
    return fn(run_context, arguments)


def _validate_output_model(registration: CapabilityRegistration, raw: Any) -> Any:
    if registration.output_model is None:
        return raw
    if isinstance(raw, registration.output_model):
        return raw
    return registration.output_model.model_validate(raw)


def _argument_keys(arguments: Any) -> list[str]:
    if isinstance(arguments, BaseModel):
        return sorted(arguments.model_fields_set)
    if isinstance(arguments, dict):
        return sorted(str(key) for key in arguments)
    return []


def _safe_argument_preview(arguments: Any) -> dict[str, Any]:
    return {"argument_keys": _argument_keys(arguments)}


def _safe_exception_message(exc: Exception) -> str:
    text = str(exc).lower()
    if any(fragment in text for fragment in ["secret", "token", "password", "credential", "api_key", "authorization"]):
        return f"{type(exc).__name__}:REDACTED"
    return f"{type(exc).__name__}:{str(exc)[:160]}"


def _run_id_from_context(context: Any) -> str | None:
    metadata = getattr(context, "metadata", {}) or {}
    candidate = metadata.get("run_id") or metadata.get("run_ref") or getattr(context, "trace_id", None)
    if not candidate:
        return None
    value = str(candidate)
    if "/" in value or "\\" in value:
        return None
    return value[:160]


def _record_capability_session_event(
    event_type: str,
    *,
    capability_name: str,
    agent_name: str,
    run_id: str | None,
    status: str,
    lifecycle_state: str,
    duration_ms: float | None = None,
    reason_codes: list[str] | None = None,
    error_code: str | None = None,
    error_summary: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    capability_ref = build_safe_ref("capability", capability_name)
    correlation_id = build_safe_ref("capability-correlation", capability_name, agent_name, run_id or "local")
    record_session_event(
        fail_closed=False,
        session_id="capability-session:local",
        run_id=run_id,
        trace_id=correlation_id,
        span_id=build_safe_ref("capability-span", correlation_id, event_type),
        correlation_id=correlation_id,
        service="capability_registry",
        surface="capability_execution",
        event_type=event_type,
        lifecycle_state=lifecycle_state,
        status=status,
        severity="error" if status in {"failed", "timeout"} else "warning" if status == "denied" else "info",
        duration_ms=duration_ms,
        safe_summary="Capability execution lifecycle recorded as a redacted summary.",
        reason_codes=reason_codes or [],
        error_code=error_code,
        error_summary=error_summary,
        input_refs=[build_safe_ref("capability-input", capability_name, "structured")],
        output_refs=[build_safe_ref("capability-output", capability_name, status)] if status == "succeeded" else [],
        redaction_summary={
            "status": "summary_only",
            "input_values_stored": False,
            "output_values_stored": False,
        },
        metadata={
            "capability_ref": capability_ref,
            "agent_ref": build_safe_ref("agent", agent_name),
            **(metadata or {}),
        },
    )
