# UAA Runtime Route Decision Binding

Status: implemented as Phase 02 of the UAA runtime parity pack.

This lane adapts the external comparison runtime route-decision preflight pattern as a
UAA-native core contract. It does not copy external reference code, does not import
external runtime packages, and does not add runtime authority.

## Implemented Repo-Safe Slice

`RouteDecisionBinding` binds a prepared turn decision to:

- actor, session, and turn safe refs
- turn contract kind
- route or surface ref
- route side-effect class
- invocation policy ref and policy version ref
- approval ref and approval-scope ref when already present
- provider/model choice refs when present
- tool, action, and resource safe refs when present
- idempotency key
- created and expiry timestamps
- content/context fingerprint refs without raw content
- redaction refs and evidence refs

`validate_route_decision_binding` rejects stale or mismatched decisions with
operator-readable statuses:

- `expired`
- `scope_changed`
- `policy_changed`
- `replay_conflict`
- `authority_blocked`
- `unsafe_payload`

The CLI inspection path is:

```bash
.venv/bin/python scripts/dev/uaa_turn_router.py route-binding --sample card-pickup --pretty
```

The CLI output is safe JSON. It omits raw prompt text, treats route decisions
as inspection-only, and grants no approval or execution authority.

## Boundaries Preserved

Route-decision binding is not approval. It cannot authorize send, retry, edit,
action start, run start, provider/model calls, tool execution, browser
automation, connector writes, plugin runtime import, unrestricted shell or
subprocess execution, remote execution, production authority, public release
claims, or broad autonomy.

Control Center may later display or initiate backend-owned binding envelopes,
but Control Center still cannot mint authority. Any future mutating route must
validate a fresh binding and still validate exact LocalApprovalAuthority scope
where mutation authority is required.

## Evidence

- `src/ultimate_ai_agent/core/decision_router/route_binding.py`
- `src/ultimate_ai_agent/core/decision_router/__init__.py`
- `scripts/dev/uaa_turn_router.py`
- `tests/test_route_decision_binding.py`
- `scripts/verify_uaa_runtime_route_decision_binding.py`

## Still Blocked

- runtime model calls
- provider SDK calls
- live web fetching
- browser automation
- connector writes
- unrestricted shell/subprocess execution
- plugin runtime import
- remote execution
- production authority
- public release claims
- broad autonomy
- raw prompt, raw response, raw provider payload, raw local path, raw log,
  credential, or secret-like persistence

## Promotion Path

Later phases can attach this validator to prepared chat turns, durable run
records, Action Inbox approval waits, and exact action receipts. Each attachment
must prove fresh binding validation, idempotency replay behavior, exact approval
scope validation where required, safe-disable behavior, redaction, CLI/API/Core
parity, route side-effect classification, and focused tests before any mutation
path can trust it.
