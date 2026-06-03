# M26 To M27 Boundary

Status: active
Current through: v0.31.1
Purpose: Record the handoff from M26 recall planning to M27 safe tool intent contracts.

M26 implements and hardens Grounded Recall Router + Evidence-Linked Context Pack
Builder contracts only. v0.30.1 enforces source_ref/source_kind consistency and
does not add runtime context injection.

v0.31.0 implements M27 Tool Broker v2 + Safe Tool Intent Contracts as
validation-only and preview-only contract logic. M27 adds safe tool intent
contracts and non-executing receipt plans; it does not add real tool execution,
shell execution, file mutation, memory writes, Event Ledger mutation, backend
execution routes, browser automation, plugin enablement, model/provider calls,
context injection, or production authority.

M28-M40 remain planned/provisional. Any future sandbox, dry-run, approved tool
execution, plugin runtime, browser automation, or production authority requires
a separate reviewed milestone prompt, its own tests, documentation, static
verifier coverage, Foundation Gate criteria, and release review.
