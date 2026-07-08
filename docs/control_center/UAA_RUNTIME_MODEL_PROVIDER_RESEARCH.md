# UAA Runtime Model Provider Research Posture

Status: Phase 07 implemented read model. This document is not runtime
authority and does not grant model, provider, web, browser, memory, connector,
or production authority.

## Full-Strength Target

UAA should eventually make model/provider and research operations feel like a
real governed cockpit:

- provider adapter readiness and exact lane status;
- secret status without exposing secret material;
- network allowlists and model metadata discovery;
- cost and latency literacy with CostGovernor hooks;
- local model lifecycle visibility;
- model-router and provider-router traces;
- research and external information posture through WebAccessGateway;
- clear truth handling where model output is proposal/evidence, not authority.

## Repo-Safe Implementation

Phase 07 adds
`contract-ref:runtime-model-provider-research-posture:v1` as
`model_provider_research_posture` inside the existing backend-owned
`GET /control-center/providers/runtime-control-plane` payload.

The read model is owned by Python Core in
`src/ultimate_ai_agent/core/providers/control_plane.py` and is inspectable with:

```bash
.venv/bin/python scripts/inspect_model_provider_control_plane.py
.venv/bin/python scripts/verify_uaa_runtime_model_provider_research.py
```

The Control Center `/models` surface renders the same posture as readable
cards. The frontend client rejects unsafe payloads that claim provider SDK
calls, remote model calls, live web fetch, browser automation, credential entry,
memory writes, action execution, context injection, production authority, or
broad autonomy.

## Truth Handling

The read model records:

- model output is proposal text or an evidence candidate;
- generated text is not a verified fact by itself;
- verified fact refs and uncertainty/unknowns are required;
- model output cannot grant memory, action, context, connector, or production
  authority.

## External Information Posture

External information remains WebAccessGateway governed and deny-by-default.
Fetched content is untrusted evidence, never instructions. Source metadata and
audit records are required before any future promotion.

The current visible lane is still limited to the existing allowlisted read-only
web evidence posture. Browser observe, browser action, provider search,
context injection, and memory writes from external content remain blocked.

## Still Blocked

- provider SDK calls;
- remote model calls by this control-plane read model;
- live web fetch by this control-plane read model;
- browser observe or browser action from this control-plane read model;
- credential entry or secret material display;
- provider output as truth or authority;
- memory/action/context escalation from model output or external content;
- connector writes;
- production authority;
- broad autonomy.

## Promotion Path

Any future promotion must be exact-lane scoped and prove approval binding,
idempotency, CostGovernor refs, redacted receipts, safe-disable or rollback
posture, route side-effect classification, CLI/API/Core parity, frontend truth
labels, and focused verifier coverage.
