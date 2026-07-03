# Provider / Model Invocation Blocker

Status: blocked, no live provider/model invocation promoted
Lane: Provider / Model Invocation
Attempted promotion: Level 2 manual foreground exact invocation
Date: 2026-07-03

## Existing Verified Posture

UAA already has a tiny exact-approved provider lane, exposed through:

- route_ref: `POST /control-center/providers/exact-approved-lanes/tiny`
- CLI inspection: `scripts/inspect_tiny_provider_invocation_lane.py`
- verifier: `scripts/verify_tiny_provider_invocation_lane.py`

The lane is contract-wired, CostGovernor-bound, idempotency-bound, receipt
aware, and redacted. It remains disabled by default.

Safe posture inspection on 2026-07-03 reported:

- status: `disabled`
- invocation_enabled: `false`
- network_call_enabled: `false`
- provider_sdk_call_enabled: `false`
- autonomous_model_call_enabled: `false`
- billing_authority_granted: `false`
- prompt_persistence_allowed: `false`
- response_persistence_allowed: `false`
- provider_exchange_persistence_allowed: `false`
- redacted_receipts_only: `true`
- receipt_state_source: `no_receipt_observed`

## Why This Was Not Unblocked

The next requested promotion requires one capped provider/model call with exact
approval, credential readiness, CostGovernor hard limits, redacted prompt and
response refs, actual usage/cost receipts, and no output authority.

That promotion was not safe in this run because:

- no operator-approved test credential ref was supplied;
- no exact live invocation approval scope was supplied for this run;
- no real max-approved USD decision and budget receipt were supplied;
- no actual usage/cost receipt store was preauthorized for a live adapter;
- default tiny live adapters remain disabled/no-execution;
- broad provider/model authority is still blocked by policy.

## Missing Contract / Test / Evidence

- test credential enrollment or revocation evidence for the exact provider;
- exact LocalApprovalAuthority grant for the one invocation scope;
- CostGovernor decision refs with max-approved USD;
- live adapter enablement proof limited to one named adapter;
- redacted receipt store proof with actual usage and actual cost refs;
- review rule for incomplete actual cost before further use;
- dogfood receipt proving no raw prompt, raw response, or provider exchange was
  persisted.

## Smallest Next Safe Action

Run a dedicated provider invocation unblock PR that performs exactly one
operator-approved test invocation through an already defined tiny live adapter,
or records a no-go if the test credential/approval/cost receipt prerequisites
are not available.

## Authority Still Blocked

- broad provider/model authority
- autonomous model calls
- provider router fallback execution
- model-output-as-truth
- model-output action execution
- memory write or context injection from model output
- background provider calls
- public beta, public release, or production authority
