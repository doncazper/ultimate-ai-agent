# v0.32.1 README Import

Status: historical release artifact
Captured at: v0.32.1
Do not use as current roadmap or current baseline after this release.
Current roadmap: docs/canonical/09_roadmap.md

## Release

v0.32.1 — M28 Hardening: Evaluator Revalidation for Raw/Secret Action Inputs.

## Scope

This release hardens M28 Approval Authority v2 by revalidating action intents,
approval grants, and action policies at evaluator time before any policy-only
allow decision. It blocks `model_copy(update=...)` bypasses for raw action
content flags, secret-like summaries and metadata, metadata refs,
`approval_test_` grant refs, expired/revoked/replayed grants, wildcard grants,
and actor/action/resource/scope mismatches.

## Non-Goals

No action execution, tool execution, shell/subprocess execution, file mutation,
memory writes, network calls, model/provider calls, browser automation,
mobile/device access, remote execution, plugin enablement, backend execution
routes, frontend execute controls, dependencies, production authority, or M29
work is added.

M29-M40 remain planned/provisional.
