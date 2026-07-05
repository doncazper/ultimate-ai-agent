# Debug Log System

The debug log system provides local, structured JSONL records for everyday troubleshooting without expanding runtime authority or exporting raw private content.

UAA also has an extreme diagnostic profile for short troubleshooting windows.
It is disabled by default and must be enabled explicitly with
`UAA_EXTREME_LOGGING_ENABLED=1`. Extreme logging is still redacted, bounded,
local-only, and safe-ref oriented; it is not a raw forensic mode.

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
- Extreme logging is disabled unless `UAA_EXTREME_LOGGING_ENABLED` is set to a
  truthy value.
- Extreme logging writes to local JSONL under `UAA_EXTREME_LOG_ROOT`, defaulting
  to `.uaa/observability/extreme_debug.jsonl`.
- `UAA_EXTREME_LOG_PREVIEW_CHARS` may raise bounded diagnostic previews up to
  the hard cap, but raw prompt, response, provider payload, terminal output,
  headers, query values, local paths, credentials, and private content remain
  denied.

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

## Extreme Logging

Normal session logging records safe lifecycle summaries. Extreme logging records
additional local diagnostic gateway metadata only when explicitly flagged on:

```bash
export UAA_EXTREME_LOGGING_ENABLED=1
export UAA_EXTREME_LOG_ROOT=.uaa
export UAA_EXTREME_LOG_PREVIEW_CHARS=2048
```

Programmatic callers can inspect the active posture:

```python
from ultimate_ai_agent.core.observability import build_extreme_debug_logging_settings

settings = build_extreme_debug_logging_settings()
assert settings.default_disabled is True
assert settings.redacted_only is True
assert settings.raw_content_stored is False
```

When disabled, UAA does not create the extreme debug JSONL file. When enabled,
API middleware records extra route pattern, status, duration, correlation, and
diagnostic posture metadata while omitting HTTP content, header values, query
values, and raw local details.

## Querying

Use `list_records()` to filter by session, run, category, or level. Use `latest()` for a bounded tail and `summary()` for counts by category and level.
