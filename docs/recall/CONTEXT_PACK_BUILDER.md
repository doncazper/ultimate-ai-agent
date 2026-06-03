# Evidence-Linked Context Pack Builder

Status: active
Current through: v0.31.0
Purpose: Define the M26 safe context-pack builder contract.

The M26 Context Pack Builder converts a Grounded Recall decision into an
evidence-linked pack of safe summaries and refs. It is a local planning
contract, not a runtime injection path.

Context packs may include:

- selected safe summaries.
- canonical, evidence, receipt, event, memory, and file refs.
- source priority summaries.
- redaction status.
- token estimate and budget summaries.

Selected items must already have validated source_ref/source_kind consistency.
The builder rejects mismatched selected items rather than turning caller-declared
source_kind into context-pack authority.

Context packs must not include:

- raw prompts.
- raw model output.
- raw file content.
- raw memory content.
- raw transcripts.
- secrets, credentials, tokens, keys, cookies, or Authorization values.
- provider payloads.

The builder does not inject context into OpenWebUI, model runtimes, prompts,
tools, memory stores, or Control Center actions.
