# v0.32.1 Master Plan

Status: historical release artifact
Captured at: v0.32.1
Do not use as current roadmap or current baseline after this release.
Current roadmap: docs/canonical/09_roadmap.md

## Objective

Harden M28 Approval Authority v2 + Action Policy Expansion so evaluator
decisions revalidate current action intent, approval grant, and action policy
state before allowing policy-only decisions.

## Deliverables

- evaluator-side revalidation for action intents, approval grants, and action
  policies.
- denial of mutated raw prompt/model/file/transcript flags.
- denial of secret-like summaries, metadata, and metadata refs.
- denial of `approval_test_` grant refs as runtime authority.
- regression tests for `model_copy(update=...)` mutation bypasses.
- Foundation Gate and static verifier probes for mutated-object bypasses.
- release notes, active docs, and archive packet.

## Boundaries

M28 remains non-executing. This patch adds no backend routes, action execution,
tool execution, shell execution, file mutation, memory write, network call,
model/provider call, browser/mobile/remote/plugin execution, frontend execute
controls, dependency, production authority, or M29 implementation.
