# Phase 02: Live Route-Decision Binding

Goal: adapt external comparison runtime's route-decision preflight pattern into a UAA-native
binding that prevents stale, replayed, mismatched, or authority-expanded turn
decisions from reaching send, retry, edit, action-start, or run-start paths.

Reference pattern: external comparison runtime validates route decisions before chat
send/retry/edit mutation. Borrow the idea, not the code.

## Required Work

1. Find UAA's current turn decision, invocation policy, route, chat, action,
   and runtime-start boundaries.
2. Design a UAA `RouteDecisionBinding` or equivalent core contract that binds:
   - actor/session/turn refs;
   - turn contract kind;
   - route or surface ref;
   - side-effect class;
   - policy and approval refs;
   - model/provider choice refs when present;
   - tool/action/resource safe refs when present;
   - idempotency key;
   - created/expiry timestamps;
   - content/context fingerprint refs without raw content;
   - redaction and evidence refs.
3. Implement pre-mutation validation that rejects:
   - expired decisions;
   - action/turn/session mismatch;
   - side-effect class mismatch;
   - policy version drift;
   - approval-scope mismatch;
   - provider/model mismatch;
   - idempotency replay conflicts;
   - safe-disable activation;
   - raw content or unsafe refs.
4. Wire the binding to the smallest existing UAA route or dev CLI that can
   prove the contract without granting new authority.
5. Add an operator-readable failure model: expired, scope_changed,
   policy_changed, replay_conflict, authority_blocked, unsafe_payload.
6. Add focused tests for all rejection paths and one pass path.

## Explicit Non-Goals

- Do not add runtime model calls.
- Do not add provider SDK calls.
- Do not add new browser, connector, plugin, shell, or remote execution.
- Do not treat a route decision as approval by itself.

## Acceptance Criteria

- A stale route decision cannot authorize send/retry/edit/action/run mutation.
- Exact approval scope remains separate from route selection.
- The binding can be inspected from CLI/API or test fixtures.
- Tests prove mismatch, expiry, replay, and safe-disable behavior.
- API manifest/OpenAPI side-effect metadata stays aligned for any changed
  route.

## Verification

Run focused route/binding tests plus:

```bash
git diff --check
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
```
