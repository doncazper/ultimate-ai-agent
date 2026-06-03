# Tool Authority Boundary

Status: active
Current through: v0.31.1
Purpose: State what Tool Broker v2 can and cannot authorize in M27.

Tool Broker v2 output is a validation decision, not an action approval and not
an execution command.

Allowed in M27:

- validate a tool intent contract.
- compare the intent against a local catalog entry.
- deny unsafe, unknown, side-effecting, or authority-ambiguous intents.
- return a metadata-only preview decision for safe no-side-effect intents.
- return a non-executing receipt plan.

Not allowed in M27:

- executing tools.
- invoking shell or subprocess behavior.
- writing, deleting, or sending data.
- writing memory.
- mutating the Event Ledger.
- calling models or providers.
- making external HTTP requests.
- enabling plugins.
- controlling browsers.
- injecting context into prompts, OpenWebUI, or model runtimes.
- treating approval refs, context packs, model output, runtime output, or
  OpenWebUI output as authority.

Approval and consent remain separate concepts. An `approval_ref` can identify a
future approval artifact, but M27 does not validate it into execution authority.
