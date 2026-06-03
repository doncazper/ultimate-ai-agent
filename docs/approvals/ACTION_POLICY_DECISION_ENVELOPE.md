# Action Policy Decision Envelope

Status: active
Current through: v0.32.0
Purpose: Define the non-executing decision shape returned by M28.

M28 action policy decisions report whether an action intent is allowed for
policy planning only. They include stable reason codes, a sanitized safe message,
binding status, and no-execution fields.

Required decision properties:

- `allowed_for_policy` may be true only for safe no-effect or read-metadata
  intents with valid policy inputs.
- `execution_authorized` is always false.
- `execution_performed` is always false.
- denied decisions include stable reason codes.
- safe messages must not echo raw invalid values, paths, secrets, tokens, or
  exception text.
- decisions do not write memory, mutate files, mutate Event Ledger records,
  call networks, call models/providers, execute tools, or dispatch actions.

The decision envelope is not production authority and is not an execution
receipt.

M29-M40 remain planned/provisional.
