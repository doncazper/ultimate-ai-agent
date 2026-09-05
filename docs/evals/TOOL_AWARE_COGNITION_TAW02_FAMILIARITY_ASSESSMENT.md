# TAW-02 Familiarity And Uncertainty Assessment

Status: bounded founder-private-dogfood implementation evidence. This document
does not grant routing, prompt, provider/model, proposal, approval, execution,
or production authority.

Acceptance-state role: `non-owner`. This slice records bounded implementation
evidence only. Mutable founder-private acceptance state is owned by the
content-addressed TAW-08 report and its two bounded active-truth reconciliations;
independent promotion is a separate gate.

## Purpose

TAW-02 derives one operator-visible familiarity state from the reviewed,
fingerprinted TAW-01 capability-awareness catalog plus content-free decision
evidence. The assessor is deterministic and model-free. It never asks a model
whether it is confident and it does not turn a classification into a proposal
or action.

The nine canonical states are:

- `familiar_supported`
- `familiar_input_required`
- `familiar_unavailable`
- `familiar_requires_approval`
- `familiar_authority_blocked`
- `capability_evidence_unavailable`
- `ambiguous`
- `novel_unsupported`
- `outcome_uncertain`

## Separate Evidence Dimensions

The assessment preserves, rather than collapses, these dimensions:

- durable start and terminal-proof posture;
- interpretation cardinality;
- deterministic and semantic match counts;
- exact capability identity;
- policy and safety decisions;
- authority-lane posture;
- current availability;
- required and invalid typed inputs;
- exact approval-validation posture; and
- answer/proposal readiness.

Semantic relevance is only match evidence. It cannot establish availability,
authority, input completeness, approval, readiness, or terminal success.

## Fail-Closed Precedence

The table-driven assessor applies the strategy contract in this order:

1. exact durable start without consistent terminal proof becomes
   `outcome_uncertain`;
2. safety or policy denial becomes `familiar_authority_blocked`;
3. missing, corrupt, stale, over-budget, or substituted capability evidence
   becomes `capability_evidence_unavailable` for a sentinel-positive turn;
4. multiple interpretations or materially distinct matches become `ambiguous`;
5. a blocked or missing graduated exact lane becomes
   `familiar_authority_blocked`;
6. a known disabled, unhealthy, stale, or absent capability becomes
   `familiar_unavailable`;
7. missing or invalid typed inputs become `familiar_input_required`;
8. a complete request in a graduated exact lane becomes
   `familiar_requires_approval` when its exact approval is still required;
9. exact, usable, complete, policy-consistent, ready evidence becomes
   `familiar_supported`; and
10. a valid current catalog with no capability match becomes
    `novel_unsupported`.

Contradictory input partitions, substituted field references, duplicate
matches, mismatched policy evidence, invalid approval claims, and exact
capabilities that are not decision-ready are rejected rather than guessed.

## Evidence And Authority Boundary

The result binds catalog, candidate envelope, operation-schema, policy,
availability, safety, and evaluation-set refs into a canonical SHA-256
assessment fingerprint. It persists no raw operator/model content, local path,
secret, or provider payload. The output carries literal false values for model
calls, provider calls, proposal construction, approval requests, execution,
and authority grants.

A `validated` approval posture must bind the exact operation, graduated
authority lane, policy snapshot, scope, and approval-evidence refs. Those refs
remain evidence identifiers only: the assessor cannot validate or mint
`LocalApprovalAuthority`, and the result still grants no execution authority.

TAW-03 remains responsible for bounded progressive retrieval. TAW-04 remains
responsible for any later evidence-only shadow integration with the Turn
Contract Router. Those later slices must preserve the existing policy,
approval, dispatcher, receipt, rollback, and safe-disable boundaries.

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_tool_aware_cognition_taw02.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_aware_cognition_taw02.py
```

The table-driven tests cover all nine states, precedence, missing/corrupt/stale
and over-budget catalogs, ambiguity, semantic versus deterministic relevance,
candidate substitution, invalid input evidence, assessment tampering, and
content-free non-authority literals.
