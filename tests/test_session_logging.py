from __future__ import annotations

import asyncio
import json
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict

import ultimate_ai_agent.api.app as api_app
from ultimate_ai_agent.core.capabilities import CapabilityPolicy, CapabilityRegistry, CapabilitySpec, RiskLevel
from ultimate_ai_agent.core.observability import (
    SessionLogStore,
    SessionLogValidationError,
    clear_default_session_log_store_cache,
    hash_sensitive_stack,
)
from ultimate_ai_agent.core.task_decomposition import CapabilityRegistryStore, CapabilityRegistryStoreConfig
from ultimate_ai_agent.core.task_decomposition.runtime import TaskDecompositionRunRequest, TaskDecompositionService
from ultimate_ai_agent.core.time import utc_now


def _session_event(**overrides):
    data = {
        "event_id": "session-event:test",
        "session_id": "session:test",
        "run_id": "run:test",
        "trace_id": "trace:test",
        "span_id": "span:test",
        "correlation_id": "correlation:test",
        "service": "api",
        "surface": "api",
        "event_type": "api.request.completed",
        "lifecycle_state": "completed",
        "status": "completed",
        "severity": "info",
        "safe_summary": "API request completed safely.",
        "reason_codes": ["API_REQUEST_METADATA_RECORDED"],
        "metadata": {"route_pattern": "/health", "method": "GET"},
        "redaction_summary": {"status": "summary_only"},
    }
    data.update(overrides)
    return data


def test_session_log_append_list_and_filters_are_bounded(tmp_path):
    store = SessionLogStore(root=tmp_path / ".uaa")
    now = utc_now()
    first = store.append(
        _session_event(
            event_id="session-event:first",
            observed_at=now,
            severity="info",
            status="completed",
        )
    )
    second = store.append(
        _session_event(
            event_id="session-event:second",
            session_id="session:other",
            run_id="run:other",
            event_type="capability.execution.failed",
            service="capability_registry",
            surface="capability_execution",
            lifecycle_state="failed",
            status="failed",
            severity="error",
            observed_at=now + timedelta(seconds=1),
            metadata={"capability_ref": "capability:test"},
        )
    )

    assert first.event_id == "session-event:first"
    assert second.event_id == "session-event:second"
    assert store.list_events(limit=1).returned_count == 1
    assert store.list_events(session_id="session:test").events[0].event_id == "session-event:first"
    assert store.list_events(run_id="run:other").events[0].event_id == "session-event:second"
    assert store.list_events(event_type="capability.execution.failed").events[0].status == "failed"
    assert store.list_events(severity="error", status="failed").events[0].event_id == "session-event:second"
    assert store.list_events(observed_after=now + timedelta(milliseconds=1)).events[0].event_id == "session-event:second"


def test_session_log_duplicate_event_id_is_rejected(tmp_path):
    store = SessionLogStore(root=tmp_path / ".uaa")
    event = _session_event(event_id="session-event:duplicate")

    store.append(event)
    with pytest.raises(SessionLogValidationError, match="SESSION_LOG_DUPLICATE_EVENT_ID"):
        store.append(event)


def test_session_log_malformed_historical_lines_do_not_crash_listing(tmp_path):
    log_path = tmp_path / ".uaa" / "observability" / "session_events.jsonl"
    log_path.parent.mkdir(parents=True)
    valid = _session_event(event_id="session-event:valid")
    log_path.write_text("not-json\n" + json.dumps(valid) + "\n", encoding="utf-8")

    store = SessionLogStore(root=tmp_path / ".uaa")
    result = store.list_events()

    assert result.returned_count == 1
    assert result.skipped_malformed_count == 1
    assert result.events[0].event_id == "session-event:valid"


@pytest.mark.parametrize(
    "unsafe_key",
    [
        "body",
        "payload",
        "raw_prompt",
        "stdout",
        "stderr",
        "token",
        "cookie",
        "authorization",
        "secret",
        "password",
        "api_key",
    ],
)
def test_session_log_rejects_raw_or_credential_metadata_keys(tmp_path, unsafe_key):
    store = SessionLogStore(root=tmp_path / ".uaa")

    with pytest.raises(SessionLogValidationError) as error:
        store.append(_session_event(metadata={unsafe_key: "redacted"}))

    assert "redacted" not in str(error.value)
    assert not store.filepath.exists()


def test_session_log_rejects_secret_like_values_without_echoing_them(tmp_path):
    store = SessionLogStore(root=tmp_path / ".uaa")
    secret_value = "abcdefghijklmnop"

    with pytest.raises(SessionLogValidationError) as error:
        store.append(_session_event(metadata={"note": f"api_key='{secret_value}'"}))

    assert secret_value not in str(error.value)
    assert not store.filepath.exists()


def test_api_middleware_records_safe_route_metadata_without_http_content(tmp_path, monkeypatch):
    monkeypatch.setenv("UAA_SESSION_LOG_ROOT", str(tmp_path / ".uaa"))
    clear_default_session_log_store_cache()
    client = TestClient(api_app.app)

    response = client.get(
        "/health?token=abcdefghijklmnop",
        headers={
            "Authorization": "Bearer abcdefghijklmnop",
            "Cookie": "session=abcdefghijklmnop",
        },
    )

    assert response.status_code == 200
    store = SessionLogStore(root=tmp_path / ".uaa")
    result = store.list_events(event_type="api.request.completed", limit=20)
    health_events = [event for event in result.events if event.metadata.get("route_pattern") == "/health"]
    assert health_events
    event = health_events[-1]
    assert event.metadata["method"] == "GET"
    assert event.metadata["status_code"] == 200
    assert event.duration_ms is not None
    payload = store.filepath.read_text(encoding="utf-8")
    assert "abcdefghijklmnop" not in payload
    assert "Authorization" not in payload
    assert "Cookie" not in payload
    assert "token=" not in payload


def test_client_error_route_stores_safe_hash_only(tmp_path, monkeypatch):
    monkeypatch.setenv("UAA_SESSION_LOG_ROOT", str(tmp_path / ".uaa"))
    clear_default_session_log_store_cache()
    client = TestClient(api_app.app)
    stack_hash = hash_sensitive_stack("traceback with local details")

    response = client.post(
        "/observability/client-errors",
        json={
            "component": "EvidencePanel",
            "surface": "evidence",
            "route_name": "evidence",
            "safe_error_message": "Client render failed safely.",
            "stack_hash": stack_hash,
            "runtime_category": "browser",
            "correlation_id": "client-correlation:test",
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    store = SessionLogStore(root=tmp_path / ".uaa")
    result = store.list_events(event_type="control_center.client_error", limit=10)
    assert result.events[0].stack_hash == stack_hash
    payload = store.filepath.read_text(encoding="utf-8")
    assert "traceback with local details" not in payload
    assert "localStorage" not in payload
    assert "Cookie" not in payload


def test_client_error_route_reports_skipped_when_session_logging_disabled(tmp_path, monkeypatch):
    monkeypatch.setenv("UAA_SESSION_LOG_ROOT", str(tmp_path / ".uaa"))
    monkeypatch.setenv("UAA_SESSION_LOG_ENABLED", "0")
    clear_default_session_log_store_cache()
    client = TestClient(api_app.app)

    response = client.post(
        "/observability/client-errors",
        json={
            "component": "EvidencePanel",
            "surface": "evidence",
            "safe_error_message": "Client render failed safely.",
            "correlation_id": "client-correlation:skipped",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "skipped"
    assert payload["data"]["reason_codes"] == ["SESSION_LOGGING_DISABLED"]
    assert not (tmp_path / ".uaa" / "observability" / "session_events.jsonl").exists()


class _ReadInput(BaseModel):
    path: str

    model_config = ConfigDict(extra="forbid")


class _ReadOutput(BaseModel):
    text: str

    model_config = ConfigDict(extra="forbid")


def _capability_spec() -> CapabilitySpec:
    return CapabilitySpec(
        id="capability:files.read_text:1.0.0",
        name="files.read_text",
        version="1.0.0",
        title="Read Text",
        description="Read a safe text reference.",
        input_schema=_ReadInput.model_json_schema(),
        output_schema=_ReadOutput.model_json_schema(),
        policy=CapabilityPolicy(risk=RiskLevel.READ_ONLY),
        source="python",
    )


def test_capability_execution_records_safe_lifecycle_refs(tmp_path, monkeypatch):
    monkeypatch.setenv("UAA_SESSION_LOG_ROOT", str(tmp_path / ".uaa"))
    clear_default_session_log_store_cache()
    registry = CapabilityRegistry()
    registry.register(
        _capability_spec(),
        lambda _ctx, args: _ReadOutput(text=f"read:{args.path}"),
        input_model=_ReadInput,
        output_model=_ReadOutput,
    )

    result = registry.execute_sync(
        "files.read_text",
        {"path": "safe-ref-only"},
        {"agent_name": "agent.alpha", "metadata": {"run_id": "run:capability-test"}},
    )

    assert result.ok is True
    store = SessionLogStore(root=tmp_path / ".uaa")
    logged = store.list_events(service="capability_registry", limit=10)
    event_types = {event.event_type for event in logged.events}
    assert {"capability.execution.started", "capability.execution.succeeded"} <= event_types
    payload = store.filepath.read_text(encoding="utf-8")
    assert "safe-ref-only" not in payload
    assert "read:safe-ref-only" not in payload


def test_capability_execution_records_denied_failed_and_timeout_safely(tmp_path, monkeypatch):
    monkeypatch.setenv("UAA_SESSION_LOG_ROOT", str(tmp_path / ".uaa"))
    clear_default_session_log_store_cache()
    registry = CapabilityRegistry()
    registry.register(
        _capability_spec().model_copy(
            update={
                "name": "files.denied",
                "id": "capability:files.denied:1.0.0",
                "policy": CapabilityPolicy(allowed_agents={"agent.allowed"}, risk=RiskLevel.READ_ONLY),
            }
        ),
        lambda _ctx, args: _ReadOutput(text=args.path),
        input_model=_ReadInput,
        output_model=_ReadOutput,
    )
    registry.register(
        _capability_spec().model_copy(update={"name": "files.failed", "id": "capability:files.failed:1.0.0"}),
        lambda _ctx, _args: (_ for _ in ()).throw(RuntimeError("api_key='abcdefghijklmnop'")),
        input_model=_ReadInput,
        output_model=_ReadOutput,
    )

    async def slow(_ctx, _args):
        await asyncio.sleep(0.05)
        return _ReadOutput(text="late")

    registry.register(
        _capability_spec().model_copy(
            update={
                "name": "files.timeout",
                "id": "capability:files.timeout:1.0.0",
                "policy": CapabilityPolicy(timeout_s=0.01, risk=RiskLevel.READ_ONLY),
            }
        ),
        slow,
        input_model=_ReadInput,
        output_model=_ReadOutput,
    )

    assert registry.execute_sync("files.denied", {"path": "safe-ref-only"}, {"agent_name": "agent.blocked"}).ok is False
    assert registry.execute_sync("files.failed", {"path": "safe-ref-only"}, {"agent_name": "agent.alpha"}).ok is False
    assert registry.execute_sync("files.timeout", {"path": "safe-ref-only"}, {"agent_name": "agent.alpha"}).ok is False

    store = SessionLogStore(root=tmp_path / ".uaa")
    logged = store.list_events(service="capability_registry", limit=20)
    event_types = {event.event_type for event in logged.events}
    assert "capability.execution.denied" in event_types
    assert "capability.execution.failed" in event_types
    assert "capability.execution.timeout" in event_types
    payload = store.filepath.read_text(encoding="utf-8")
    assert "abcdefghijklmnop" not in payload
    assert "safe-ref-only" not in payload
    assert '"text":"late"' not in payload


def test_task_decomposition_records_safe_run_and_node_correlation(tmp_path, monkeypatch):
    monkeypatch.setenv("UAA_SESSION_LOG_ROOT", str(tmp_path / ".uaa"))
    clear_default_session_log_store_cache()
    store = CapabilityRegistryStore(CapabilityRegistryStoreConfig(registry_path=str(tmp_path / "registry.json")))
    service = TaskDecompositionService(registry_store=store)
    service.ensure_examples()

    result = asyncio.run(service.run(TaskDecompositionRunRequest(raw_request="Summarize this request directly.")))

    assert result.execution is not None
    log_store = SessionLogStore(root=tmp_path / ".uaa")
    logged = log_store.list_events(service="task_decomposition", limit=100)
    event_types = {event.event_type for event in logged.events}
    assert "task.plan.created" in event_types
    assert "task.plan.execution_started" in event_types
    assert "task.plan.execution_completed" in event_types
    assert "task.node.started" in event_types
    assert "task.node.succeeded" in event_types
    assert all(event.run_id for event in logged.events)
    assert any(event.receipt_refs for event in logged.events)
    payload = log_store.filepath.read_text(encoding="utf-8")
    assert "Summarize this request directly" not in payload
    assert "Processed request with" not in payload
