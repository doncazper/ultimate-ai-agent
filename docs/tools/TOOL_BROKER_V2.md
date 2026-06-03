# Tool Broker v2

Status: active
Current through: v0.31.1
Purpose: Define the M27 validation-only Tool Broker v2 contract.

M27 implements Tool Broker v2 as deterministic local contract logic for safe
tool intent review. It accepts typed `ToolIntent` objects, checks them against a
typed catalog, and returns `ToolIntentDecision` records. A decision can allow
metadata-only preview, but it cannot execute a tool.

Tool Broker v2 is preview-only and validation-only:

- no real tool execution.
- no tool execution.
- no shell execution.
- no file write or delete.
- no memory write.
- no Event Ledger mutation.
- no network call.
- no external network call.
- no web search.
- no browser automation.
- no plugin enablement.
- no model/provider call.
- no context injection.
- no backend execution route.
- no production authority.

`approval_ref` values are identifiers only. They are not authority and cannot
turn a denied or side-effecting intent into an allowed execution.

Context packs are not authority. Context-pack refs may describe planning context in
future milestones, but M27 does not let context packs authorize tool execution.

Safe preview decisions are non-executing receipt plans only.
