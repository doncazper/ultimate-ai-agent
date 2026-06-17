# Debug Log System

The debug log system provides local, structured JSONL records for everyday troubleshooting without expanding runtime authority or exporting raw private content.

## Categories

The core categories are:

- `gateway`: API or gateway boundary request metadata, status, and latency.
- `user`: user action summaries and user refs.
- `prompt`: prompt refs, safe summaries, redacted bounded previews, and content fingerprints.
- `error`: safe error messages, error codes, redacted details, and failure status.
- `session`: session lifecycle and state changes.
- `terminal`: command refs, exit codes, latency, and redacted bounded output previews.
- `system`: internal diagnostic records.
- `security`: security-review or policy diagnostic records.

## Safety Rules

- Logs are local JSONL only when the caller provides a file path.
- Raw prompts, raw terminal output, raw provider payloads, raw response bodies, and raw private content are not stored.
- Prompt and terminal helpers store a bounded redacted preview plus a SHA-256 fingerprint of the original text.
- Credential assignments, bearer values, PEM blocks, email addresses, and local absolute paths are redacted before persistence.
- Records reject `raw_content_stored=True`.
- Metadata rejects raw-content field names such as `raw_prompt`, `raw_terminal_output`, and `raw_provider_payload`.
- The system adds no external logging service, network delivery, backend route, Control Center control, model/provider call, memory write, context injection, dependency, or production authority.

## Usage

```python
from ultimate_ai_agent.core.observability import DebugLogStore

logs = DebugLogStore("reports/debug/session.jsonl")
logs.log_session(session_id="sess_123", source="runner", session_status="started")
logs.log_gateway(
    session_id="sess_123",
    source="api",
    method="GET",
    route="/api/manifest",
    status_code=200,
    latency_ms=14,
)
logs.log_prompt(
    session_id="sess_123",
    source="model_router",
    prompt_ref="prompt:sess_123",
    prompt_text="Raw prompt text is redacted and bounded before storage.",
)
logs.log_terminal(
    session_id="sess_123",
    source="terminal",
    command_ref="command:pytest",
    output_text="Terminal output is also redacted and bounded.",
    exit_code=0,
)
```

Callers that only need in-memory collection can instantiate `DebugLogStore()` without a path.

## Querying

Use `list_records()` to filter by session, run, category, or level. Use `latest()` for a bounded tail and `summary()` for counts by category and level.

