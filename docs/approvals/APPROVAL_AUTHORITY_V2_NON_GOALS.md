# Approval Authority v2 Non-Goals

Status: active
Current through: v0.32.0
Purpose: Define what M28 intentionally does not implement.

M28 does not add:

- action execution.
- tool execution.
- shell or subprocess execution.
- file mutation.
- memory writes.
- Event Ledger mutation.
- network calls.
- model/provider calls.
- browser automation.
- mobile/device access.
- remote execution.
- plugin enablement.
- backend action, approval, tool, plugin, or shell execution routes.
- Control Center execute controls.
- dependencies.
- production approval authority.
- wildcard approvals.
- raw or secret-like action input handling.
- M29 implementation.

Approval Authority v2 is a contract/policy/decision layer only. It can deny or
allow for policy planning, but it cannot run, dispatch, mutate, send, connect,
enable, or execute.

M29-M40 remain planned/provisional.
