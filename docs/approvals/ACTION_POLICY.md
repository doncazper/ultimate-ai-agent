# Action Policy

Status: active
Current through: v0.32.0
Purpose: Define non-executing M28 action policy evaluation.

M28 action policy evaluates structured action intents and returns policy
decisions only. It can allow a safe no-effect or read-metadata action for policy
planning with `execution_authorized=False` and `execution_performed=False`.

Action policy denies:

- action execution, tool execution, shell execution, and destructive actions.
- file mutation, memory writes, Event Ledger mutation, network calls, and
  model/provider calls.
- browser, mobile/device, remote, and plugin actions.
- wildcard, expired, revoked, replayed, or mismatched approval grants.
- `approval_ref` alone, `approval_test_`, and `consent_ref` alone.
- model, memory, context-pack, or tool-intent refs as authorization.
- raw prompt, model, file, transcript, or secret-like action inputs.

Action policy decisions are non-authoritative planning records. They do not run,
dispatch, connect, send, mutate, approve production access, or create backend
execution routes.

M29 remains planned/provisional.
