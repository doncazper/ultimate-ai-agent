# Provider Draft/Summarize Micro-Lane

Status: exact core/CLI lane, fixture-proven; default Control Center provider invocation remains blocked

This lane turns one exact-approved tiny provider receipt into a local
draft/summarize proposal for operator review. It does not create broad
provider/model authority.

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

## Still Blocked

- Autonomous provider/model calls.
- Provider SDK calls.
- Broad provider routing or fallback from UI.
- Model output as truth.
- Memory write or context injection from model output.
- Connector send/write.
- Action execution from model output.
- Background provider calls.
- Public beta, public release, production readiness, or production authority.

## Evidence

- `src/ultimate_ai_agent/core/providers/draft_summarize.py`
- `scripts/inspect_provider_draft_summarize_lane.py`
- `tests/test_provider_draft_summarize_lane.py`
- `tests/test_tiny_provider_invocation_lane.py`
- `tests/test_tiny_live_provider_adapter.py`
- `tests/test_tiny_live_provider_adapter_receipts.py`
