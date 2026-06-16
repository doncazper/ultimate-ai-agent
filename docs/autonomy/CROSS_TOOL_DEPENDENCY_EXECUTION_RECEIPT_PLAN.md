# Cross-Tool Dependency Execution Receipt Plan

M136 receipt plans are no-effect receipt plans. They store safe summaries, safe
refs, dependency graph refs, dependency order refs, safe tool refs, dry-run plan
refs, policy refs, risk refs, audit refs, replay refs, revocation refs, and
kill-switch refs only.

They do not store raw tool payloads, raw prompts, raw provider payloads, raw
private content, secrets, dependency execution output, tool execution output,
connector output, browser output, model output, memory writes, context
injection payloads, backend route payloads, or production authority state.
