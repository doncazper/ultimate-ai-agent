# Ultimate AI Agent Version

Current active baseline: **v0.31.0**

v0.31.0 implements M27 Tool Broker v2 + Safe Tool Intent Contracts. It adds
deterministic local validation-only contracts for tool targets, input
boundaries, catalog entries, tool intents, tool decisions, manifests, and
non-executing receipt plans. It allows safe metadata-only preview decisions
while denying unknown tools, target mismatches, side effects, approval refs as
authority, context packs as authority, caller risk downgrades, hidden side
effects, raw content, secret-like content, model output, runtime output, and
OpenWebUI output.

It adds no real tool execution, shell/subprocess behavior, file mutation, memory
writes, Event Ledger mutation, backend tool execution routes, Control Center
execute controls, external network calls, web search, browser automation,
Computer Use, plugin enablement, model/provider calls, local LLM calls,
retrieval/RAG/vector/embedding behavior, context injection runtime,
dependencies, M28 work, or production authority. OpenAPI path count remains
`74`. M28-M40 remain planned/provisional.
