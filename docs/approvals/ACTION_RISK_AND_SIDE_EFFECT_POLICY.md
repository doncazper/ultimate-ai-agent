# Action Risk and Side-Effect Policy

Status: active
Current through: v0.32.1
Purpose: Define which action intents are safe for M28 policy decisions.

M28 permits only no-effect and read-metadata policy decisions. Action risk and
side-effect metadata cannot downgrade or hide a mutating, executing, network,
model, browser, mobile, remote, plugin, shell, destructive, or credential-access
intent.

Denied side effects include:

- file mutation.
- memory writes.
- Event Ledger mutation.
- network calls.
- model/provider calls.
- browser automation.
- mobile/device access.
- remote execution.
- plugin enablement.
- shell/subprocess execution.
- destructive or credential-access behavior.

Safe read-metadata decisions remain policy-only with
`execution_authorized=False` and `execution_performed=False`.

M29-M40 remain planned/provisional.
