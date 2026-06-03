# v0.32.0 README Import

Status: historical release artifact
Captured at: v0.32.0
Do not use as current roadmap or current baseline after this release.
Current roadmap: docs/canonical/09_roadmap.md

## Release

v0.32.0 / M28 — Approval Authority v2 + Action Policy Expansion.

## Scope

This release adds policy-only approval authority and action-policy contracts. It
binds actor/action/resource/scope, denies wildcard/expired/revoked/replayed/
mismatched grants, denies approval_ref and approval_test_ as authority, rejects
raw or secret-like action inputs, and returns non-authoritative receipt plans.

## Non-Goals

No action execution, tool execution, shell/subprocess execution, file mutation,
memory writes, network calls, model/provider calls, browser automation,
mobile/device access, remote execution, plugin enablement, backend execution
routes, frontend execute controls, dependencies, production authority, or M29
work is added.

M29-M40 remain planned/provisional.
