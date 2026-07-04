# Provider Draft/Summarize Micro-Lane

Status: exact core/CLI lane, fixture-proven; default Control Center provider invocation remains blocked

This lane turns one exact-approved tiny provider receipt into a local
draft/summarize proposal for operator review. It does not create broad
provider/model authority.

## Full-strength version

The full product goal is provider-assisted drafting and summarization that can
use approved live credentials, selected local context, explicit cost limits,
operator-visible receipts, Proof Detail, Trust posture, and follow-up review
without making model output truth or action authority.

## Repo-safe beta-09 version

The current repo-safe beta-09 version is a core/CLI wrapper over the existing
tiny exact-approved provider lane. Default inspection is blocked/no-execution.
The demo fixture proves the exact path with an injected transient test
credential, exact approval scope, CostGovernor posture, receipt store, and
scoped transport while reporting `real_provider_network_performed: false`.
Proof and Trust expose this as inspection-only state; default Control Center
provider invocation remains blocked and no provider-draft API route or UI
provider-call button is added.

Durable records omit the draft preview. A successful exact fixture may return a
bounded redacted draft preview transiently to the requester, while durable
provider receipts and durable draft records keep safe refs only.

## Scope

- Core contract: `provider-draft-summarize-lane:exact-approved:v1`
- CLI inspection: `python scripts/inspect_provider_draft_summarize_lane.py`
- Provider dependency: the existing tiny exact-approved provider invocation lane
- Output posture: draft/proposal only, never truth or action authority

The lane accepts safe refs for selected local context and safe prompt envelope
refs. The provider request remains the existing safe-ref-only
`TinyProviderInvocationRequest`.

## What Is Implemented

- Default inspection reports blocked/no-execution posture.
- Fixture inspection proves the exact path with injected transient credential,
  exact LocalApprovalAuthority grant, CostGovernor posture, receipt store, and
  scoped transport.
- Successful exact provider decisions can return a bounded redacted draft
  preview to the requester.
- Durable provider receipts and durable draft records omit the draft preview and
  store safe refs only.

## Blocked / needs authority

- Autonomous provider/model calls.
- Provider SDK calls.
- Broad provider routing or fallback from UI.
- Default Control Center provider invocation.
- Default live provider network calls.
- Raw prompt, raw response, or provider exchange persistence.
- Model output as truth.
- Memory write or context injection from model output.
- Connector send/write.
- Action execution from model output.
- Background provider calls.
- Public beta, public release, production readiness, or production authority.

## Exact promotion path

Promotion beyond beta-09 requires a separate PR with a real operator-approved
test credential, exact provider/model/credential refs, LocalApprovalAuthority
scope validation, CostGovernor decision, max-approved USD, idempotency,
receipt-store-before-network, complete usage/cost receipts, safe-disable and
rollback posture, CLI/API/UI parity, redaction tests, Proof Detail, Trust
updates, and route manifest/OpenAPI truth before any default UI/provider
invocation can exist.

## Evidence

- `src/ultimate_ai_agent/core/providers/draft_summarize.py`
- `scripts/inspect_provider_draft_summarize_lane.py`
- `scripts/verify_beta_09_provider_draft_preview.py`
- `tests/test_provider_draft_summarize_lane.py`
- `tests/test_beta_09_provider_draft_preview_verifier.py`
- `tests/test_tiny_provider_invocation_lane.py`
- `tests/test_tiny_live_provider_adapter.py`
- `tests/test_tiny_live_provider_adapter_receipts.py`
