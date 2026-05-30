# 46 — Result and Error Envelope

Status: Active foundation contract, v0/provisional until Foundation Gate.

## Purpose

All foundation services should return consistent result shapes. The Orchestrator, Tool Broker, Memory Service, File Manager, Model Router, Provider Router, Event Ledger, and future scanners should not invent incompatible response formats.

## Core rule

> Every service call returns either a `ResultEnvelope` with `success=true` and `data`, or a `ResultEnvelope` with `success=false` and an `ErrorEnvelope`. Raw exceptions should not cross service boundaries.

## ResultEnvelope fields

```text
success
operation
service
run_id
step_id
trace_id
correlation_id
data
error
warnings
evidence
cost_attribution
latency_ms
redactions_applied
rollback_ref
classification
created_at
```

## ErrorEnvelope fields

```text
code
category
message
safe_message
severity
retryable
user_action_required
details_redacted
source
caused_by
```

## Categories

```text
validation_error
authentication_error
authorization_error
consent_denied
policy_denied
rate_limited
provider_error
tool_error
model_error
not_found
conflict
timeout
internal_error
security_blocked
```

## Rules

1. `message` may be internal but must be redaction-safe before logging.
2. `safe_message` is user-facing and must not contain secrets or sensitive payloads.
3. Tool and provider errors must not expose raw credentials, authorization headers, cookies, or private request bodies.
4. Mutable operations should include `rollback_ref` or a documented reason rollback is unavailable.
5. Every error that stops a run should be recorded in the Event Ledger.

## Example

```json
{
  "success": false,
  "operation": "file.write",
  "service": "file_manager",
  "run_id": "run_123",
  "step_id": "step_007",
  "trace_id": "trace_abc",
  "correlation_id": "corr_123",
  "data": null,
  "error": {
    "code": "POLICY_DENIED_PATH",
    "category": "policy_denied",
    "message": "Path outside allowed project workspace",
    "safe_message": "The file write was blocked because the path is outside the allowed workspace.",
    "severity": "medium",
    "retryable": false,
    "user_action_required": false,
    "details_redacted": true,
    "source": "tool_broker",
    "caused_by": []
  },
  "warnings": [],
  "evidence": [],
  "cost_attribution": null,
  "latency_ms": 14,
  "redactions_applied": ["path_normalization"],
  "rollback_ref": null,
  "classification": "project_private",
  "created_at": "2026-05-29T00:00:00Z"
}
```
