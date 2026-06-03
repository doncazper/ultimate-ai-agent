# Tool Intent Receipt Plan

Status: active
Current through: v0.32.0
Purpose: Define non-executing receipt plans for M27 tool intent previews.

M27 receipt plans are planning artifacts emitted with safe preview decisions.
They do not prove execution, and they do not write to the Event Ledger.

A receipt plan may include:

- receipt plan ref.
- intent ref.
- tool id.
- safe summary.
- metadata refs.
- confirmation that execution was not performed.
- confirmation that side effects were not performed.

A receipt plan must not include:

- raw tool input.
- raw tool output.
- secret-like values.
- model output.
- runtime output.
- OpenWebUI output.
- proof of tool execution.
- Event Ledger mutation.
- memory write evidence.

Receipt plans are useful for review and future approval design, but they remain
non-authoritative in M27.
