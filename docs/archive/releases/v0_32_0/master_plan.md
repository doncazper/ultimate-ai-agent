# v0.32.0 Master Plan

Status: historical release artifact
Captured at: v0.32.0
Do not use as current roadmap or current baseline after this release.
Current roadmap: docs/canonical/09_roadmap.md

## Objective

Implement M28 Approval Authority v2 + Action Policy Expansion as a contract-only
policy and decision layer.

## Deliverables

- Approval Authority v2 contracts.
- Action Policy contracts.
- actor/action/resource/scope binding.
- expiry, revocation, replay, wildcard, mismatch, and arbitrary-ref denial.
- raw and secret-like action input rejection.
- non-authoritative approval receipt plans.
- regression tests.
- Foundation Gate and static verifier coverage.
- release notes, active docs, and archive packet.

## Boundaries

M28 remains non-executing. It adds no backend routes, action execution, tool
execution, shell execution, file mutation, memory write, network call,
model/provider call, browser/mobile/remote/plugin execution, frontend execute
controls, dependency, production authority, or M29 implementation.
