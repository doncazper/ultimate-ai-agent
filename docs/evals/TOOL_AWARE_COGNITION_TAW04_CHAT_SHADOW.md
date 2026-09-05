# TAW-04 Chat Shadow Integration

Status: bounded implementation evidence. This slice is
evidence-only shadow routing. It does not change the accepted chat route,
assemble model context, invoke a model/provider, construct a proposal, request
approval, execute a capability, fetch the web, activate a skill, or grant
authority.

Acceptance-state role: `non-owner`.
Canonical mutable-state owner: `docs/evals/TOOL_AWARE_COGNITION_TAW08_ACCEPTANCE.md`.
This document records implementation evidence only; it cannot assert or
reconcile mutable founder-private status. Only that owner may perform bounded
active-truth reconciliation. Independent promotion remains a separate gate.

## Purpose

TAW-04 adds a deterministic Python Core decision between the merged TAW-02
familiarity assessment and the future chat integration boundary. The decision
records what tool-aware routing would have considered while the accepted legacy
direct-chat path remains the only operator-visible route. It adds zero model
calls and makes zero model-visible manifests.

The output binds the exact familiarity, current TAW-01 catalog, observation
time, and optional TAW-03 hydration fingerprints; the accepted legacy route;
the safe-disable ref; reason refs; selected operation refs; derived
material-effect refs; clarification posture; and a canonical decision
fingerprint. Public boundaries revalidate copied Pydantic instances and the
complete action-state matrix so a mutated copy cannot bypass route, state, or
fingerprint checks.

## Evidence-Only Decisions

The shadow decision can record only these postures:

- preserve the accepted direct-chat route;
- record a capability candidate without constructing a proposal;
- recommend a future focused clarification in shadow evidence only;
- block capability proposal posture; or
- record that durable terminal proof remains uncertain.

A clarification is recommended only when an already validated TAW-02
`ambiguous` assessment names candidates whose exact current TAW-01 catalog
envelopes derive at least two distinct material-effect classes. Callers cannot
provide or substitute those effect refs. Same-effect or otherwise non-material
ambiguity does not interrupt direct chat. Shadow recommendations never render a
question or change the current response.

Missing, corrupt, stale, unreadable, or over-budget awareness state engages the
exact safe-disable ref, discards derived assessment/hydration evidence, blocks
capability selection, and preserves ordinary no-tool chat on the legacy route.
A valid TAW-02 `capability_evidence_unavailable` assessment is handled with the
same proposal-blocking posture. This fallback does not misclassify the request
as unsupported.

Valid awareness is revalidated at the supplied observation time against the
bound catalog, catalog epoch, availability epoch, policy snapshot, and catalog
fingerprint. A stale replay or caller-selected route is rejected before a
shadow decision is materialized.

## Model And Authority Boundary

Shadow decisions contain literal invariants for:

- the legacy and operator-visible route being identical;
- zero extra model calls;
- no model-context change and no model-visible manifest refs;
- no prompt assembly or hidden skill activation;
- no proposal, approval request, execution, provider call, network access, web
  fetch, or authority grant; and
- ordinary no-tool chat remaining available.

Selected operation refs are safe evidence refs only. Even when TAW-03
hydration is supplied, every manifest must match the exact per-operation
envelope-and-schema tuple in the revalidated current catalog. Only
proposal-eligible manifests bound to exact TAW-02 candidate refs can be
recorded, and none is inserted into a prompt in shadow mode.

## Inspection And Adversarial Coverage

`build_chat_shadow_inspection` creates one redacted Python Core projection with
both CLI and API inspection contract refs. Future surfaces must serialize this
same projection rather than reimplement routing logic in a shell or UI. This
slice does not add a route or Control Center action.

`build_catalog_injection_cases` predeclares one adversarial case ref and one
schema-limited rendering-path ref for capability and operation identifiers,
aliases, availability, description, effect metadata, examples, input/output
schemas, operation metadata, preconditions, provenance/review metadata,
risk/approval metadata, rollback, and terminal-proof metadata. Every case is
explicitly non-model-visible in shadow mode.

The response-level injection census remains
`blocked_until_no_effect_active_replay`. No response exists in evidence-only
shadow mode, so this implementation does not invent a zero-event result or
shrink the future denominator. Promotion must later run the complete accepted
no-effect active replay and require zero instruction-following events before
any model-visible integration.

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_tool_aware_cognition_taw04.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_aware_cognition_taw04.py
```

The focused tests cover every safe-disable status, direct-chat preservation,
zero-extra-call and non-authority literals, material-effect clarification,
non-material ambiguity, capability-evidence failure, outcome uncertainty,
copied-instance route substitution, stale-catalog replay, cross-candidate
hydration tuple substitution, recomputed action-state drift, shared inspection
projection, and the complete predeclared injection-field inventory.

## Next Slice

TAW-05 remains responsible for exact terminal receipt binding and governed,
recomputable outcome projections. No response-level promotion, runtime model
integration, online training, or policy/alias learning is granted here.
