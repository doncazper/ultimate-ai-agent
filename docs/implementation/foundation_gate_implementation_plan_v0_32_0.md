# Foundation Gate Implementation Plan v0.32.0

Status: active
Current through: v0.32.0
Purpose: Document M28 Foundation Gate coverage.

v0.32.0 adds focused Foundation Gate criteria for Approval Authority v2 + Action
Policy Expansion.

## Criteria

- `m28_approval_authority_v2_action_policy_safe`
- `m28_action_policy_openapi_routes_unchanged`
- `m28_m29_remains_future`

## Coverage

The gate verifies that M28:

- provides the Approval Authority v2 package and docs.
- keeps action execution, tool execution, file mutation, memory writes, network
  calls, model/provider calls, browser/mobile/remote/plugin execution, shell
  execution, backend execution routes, and production authority disabled.
- denies approval_ref alone, approval_test_, consent_ref alone, wildcard,
  expired, revoked, replayed, mismatched, model, memory, context-pack, and
  tool-intent authority probes.
- rejects raw and secret-like action inputs.
- allows safe read-metadata policy decisions only with
  `execution_authorized=False` and `execution_performed=False`.
- keeps OpenAPI path count at `74`.
- keeps M29-M40 planned/provisional.

This plan adds no runtime execution capability.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can influence agent behavior.
