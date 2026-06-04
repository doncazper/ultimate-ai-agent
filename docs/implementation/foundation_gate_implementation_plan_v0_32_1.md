# Foundation Gate Implementation Plan v0.32.1

Status: active
Current through: v0.32.1
Purpose: Document M28 evaluator revalidation Foundation Gate hardening.

v0.32.1 strengthens existing M28 Foundation Gate coverage for Approval
Authority v2 + Action Policy Expansion. It adds mutated-object probes to ensure
that evaluator decisions revalidate action intents and approval grants before
any policy-only allow decision.

## Criteria

- `m28_approval_authority_v2_action_policy_safe`
- `m28_action_policy_openapi_routes_unchanged`
- `m28_m29_remains_future`

## Added Coverage

The gate now verifies that M28 denies:

- `ActionIntent.model_copy(update={"contains_raw_prompt": True})`
- `ActionIntent.model_copy(update={"contains_raw_model_output": True})`
- `ActionIntent.model_copy(update={"metadata": {"token": "..."}})`
- `ApprovalGrant.model_copy(update={"grant_ref": "approval_test_..."})`

The gate continues to verify that safe read-metadata policy decisions are
policy-only, non-executing, and non-authoritative.

This plan adds no runtime execution capability.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can influence agent behavior.
