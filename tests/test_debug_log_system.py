import json

import pytest

from ultimate_ai_agent.core.observability import (
    DebugLogCategory,
    DebugLogRecord,
    DebugLogStore,
    redact_debug_text,
)


def test_debug_log_store_records_core_debug_categories(tmp_path):
    log_path = tmp_path / "debug.jsonl"
    store = DebugLogStore(log_path, max_preview_chars=96)

    store.log_session(session_id="sess_1", source="test", session_status="started")
    store.log_gateway(
        session_id="sess_1",
        source="api",
        method="get",
        route="/api/manifest",
        status_code=200,
        latency_ms=12,
    )
    store.log_user(
        session_id="sess_1",
        source="ui",
        user_ref="user:test",
        action_summary="Asked for debug logs.",
    )
    store.log_prompt(
        session_id="sess_1",
        source="model_router",
        prompt_ref="prompt:sess_1",
        prompt_text="Plan the task. api_key='abcdef1234567890' contact me@example.com.",
    )
    store.log_terminal(
        session_id="sess_1",
        source="terminal",
        command_ref="command:pytest",
        output_text="failed at /Users/example/project/test.py with token=abcdef1234567890",
        exit_code=1,
    )
    store.log_error(
        session_id="sess_1",
        source="runner",
        safe_message="Command failed",
        error_type="CalledProcessError",
        error_code="pytest_failed",
        details_text="Traceback in /Users/example/project with Authorization: Bearer abcdef1234567890",
    )

    records = store.list_records(session_id="sess_1")
    assert [record.category for record in records] == [
        "session",
        "gateway",
        "user",
        "prompt",
        "terminal",
        "error",
    ]

    prompt_records = store.list_records(category=DebugLogCategory.prompt)
    assert len(prompt_records) == 1
    assert prompt_records[0].content_sha256
    assert prompt_records[0].raw_content_stored is False
    assert "[REDACTED_CREDENTIAL]" in prompt_records[0].safe_preview
    assert "[REDACTED_EMAIL]" in prompt_records[0].safe_preview

    terminal_records = store.list_records(category="terminal")
    assert terminal_records[0].level == "error"
    assert "[REDACTED_PATH]" in terminal_records[0].safe_preview
    assert "[REDACTED_CREDENTIAL]" in terminal_records[0].safe_preview

    summary = store.summary(session_id="sess_1")
    assert summary.total_records == 6
    assert summary.category_counts["prompt"] == 1
    assert summary.error_count == 2

    persisted = log_path.read_text(encoding="utf-8")
    assert "abcdef1234567890" not in persisted
    assert "/Users/example/project" not in persisted
    assert "me@example.com" not in persisted

    reloaded = DebugLogStore(log_path)
    assert len(reloaded.list_records(session_id="sess_1")) == 6


def test_debug_log_store_rejects_duplicate_ids():
    store = DebugLogStore()
    record = DebugLogRecord(
        log_id="log_duplicate",
        category=DebugLogCategory.system,
        session_id="sess_1",
        source="test",
        message="Recorded once.",
    )

    store.append(record)
    with pytest.raises(ValueError, match="Duplicate debug log_id"):
        store.append(record)


def test_debug_log_records_deny_raw_content_flags_and_raw_metadata_keys():
    with pytest.raises(ValueError, match="DEBUG_LOG_RAW_CONTENT_DENIED"):
        DebugLogRecord(
            category=DebugLogCategory.prompt,
            session_id="sess_1",
            source="test",
            message="Unsafe record.",
            raw_content_stored=True,
        )

    with pytest.raises(ValueError, match="DEBUG_LOG_RAW_FIELD_DENIED"):
        DebugLogRecord(
            category=DebugLogCategory.prompt,
            session_id="sess_1",
            source="test",
            message="Unsafe metadata.",
            metadata={"raw_prompt": "do not store this"},
        )


def test_debug_redaction_is_bounded_and_fingerprinted():
    redacted = redact_debug_text(
        "hello " + "x" * 200 + " password=superlongpassword",
        max_chars=64,
    )

    assert len(redacted.preview) <= 64
    assert redacted.truncated is True
    assert len(redacted.sha256) == 64
    assert "superlongpassword" not in redacted.preview
    assert "credential_assignment" in redacted.redactions_applied


def test_debug_log_jsonl_records_are_valid_json(tmp_path):
    log_path = tmp_path / "debug.jsonl"
    store = DebugLogStore(log_path)
    store.log_gateway(
        session_id="sess_json",
        source="api",
        method="post",
        route="/api/events/validate",
        status_code=422,
        latency_ms=5,
    )

    [line] = log_path.read_text(encoding="utf-8").splitlines()
    payload = json.loads(line)
    assert payload["category"] == "gateway"
    assert payload["status_code"] == 422
    assert payload["latency_ms"] == 5

