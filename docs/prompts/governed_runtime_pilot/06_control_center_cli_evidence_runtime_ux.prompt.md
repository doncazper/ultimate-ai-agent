# Phase 06: Control Center, CLI, Evidence, And Runtime UX

Goal: make governed runtime visible and operable through both CLI and Control
Center without UI-only truth.

## Required CLI

Add or extend commands equivalent to:

```bash
uaa runtime status
uaa runtime capabilities
uaa runtime invocations list
uaa runtime invocations show <runtime-invocation-ref>
uaa runtime receipts show <runtime-receipt-ref>
uaa actions approve <approval-ref>
uaa actions deny <approval-ref>
uaa runtime safe-disable
```

CLI output must use safe refs and bounded redacted summaries.

## Required Control Center UX

Add or extend operator surfaces for:

- runtime profile/status;
- local model readiness and disabled state;
- command runtime readiness and disabled state;
- pending runtime approvals;
- exact approval envelope details;
- execution progress/result;
- evidence receipt timeline;
- safe-disable state;
- blocked authority list.

The UI must call backend read models and mutating APIs. It must not create
product behavior only in React state.

## Evidence Requirements

Every runtime event must have a safe receipt path:

- invocation requested;
- policy decision;
- approval requested;
- approval accepted/denied/expired;
- execution started;
- execution completed/failed/timed out;
- safe-disable invoked.

No durable raw prompts, raw model responses, raw command output, raw local
paths, raw logs, usernames, hostnames, env dumps, credentials, or secret-like
values.

## Acceptance Criteria

- CLI and Control Center show the same backend-owned runtime truth.
- Operator-critical flows are not raw JSON.
- Loading/error states do not imply authority that is unavailable.
- Redaction tests cover visible strings.
- Evidence timeline can be inspected by safe ref.

## Verification

Run focused CLI/UI/evidence tests plus:

```bash
git diff --check
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
make frontend-check
.venv/bin/python scripts/verify_documentation_integrity.py
```
