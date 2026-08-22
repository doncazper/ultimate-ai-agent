# ECO-010 Deterministic Proposal Intelligence

Status: implemented as a bounded proposal-only Python Core lane
Baseline: v0.104.0 / 0.104.0
Date: 2026-08-22

## Accepted Scope

ECO-010 turns already-normalized, redacted, cited facts into deterministic
event, task, person, commitment, and meeting candidates. Every fact is bound to
an independently supplied current source-revision ref. The result preserves
canonical owner, workspace and privacy scope, citations, confidence,
ambiguities, missing evidence, stale-source posture, and a human review state.

Meeting candidates target Calendar-owned Event truth; person candidates target
Identity; task and commitment candidates target Tasks. The extractor creates no
target record and does not change the ownership map.

## Input Contract

`ProposalExtractionRequest` accepts at most 64 already-normalized
`ProposalFact` records and the current source-revision binding for every source
artifact. Facts contain bounded safe summaries and refs only. Raw message,
meeting, document, provider, or source content is not accepted or fetched.

The deterministic baseline does not infer facts from prose. Source-specific
normalization and any later model-assisted candidate generation require their
own accepted milestones. A model result may become only another cited,
uncertain proposal input; it cannot become authority.

## Output And Review Posture

Each candidate is one of:

- `ready_for_review` when its source revision is current, confidence is at
  least medium, and no ambiguity or required-evidence gap remains;
- `needs_review` when confidence is low or evidence/ambiguity remains; or
- `blocked_stale_source` when the fact is not bound to the current source
  revision.

Event and meeting facts require time evidence. Meeting facts also require at
least one participant ref. Person facts require an identity subject ref. These
gaps remain visible rather than being silently invented.

## Surfaces

- Python Core: `src/ultimate_ai_agent/core/ecosystem/proposals.py`
- Validation-only API: `POST /control-center/proposal-intelligence/extract`
- Repo-local synthetic-fixture inspection: `scripts/inspect_eco_010_proposals.py`
- Focused verifier: `scripts/verify_queue_v2_q27_proposal_intelligence.py`

The API and synthetic-only CLI expose the same Python-owned result. The CLI has
no file-input option or local source-read path. There is no product route
or primary Control Center workflow in this shared-core milestone; later Inbox,
Calendar, Tasks, CRM, or meeting UI must consume typed proposal refs without
duplicating canonical records.

## Authority Boundary

This lane performs no source read, network request, connector operation, model
or provider call, approval grant, ChangeSet creation, target mutation, direct
commit, external write, browser action, shell execution, background workflow,
public release, or production-authority promotion. Review is the terminal
state of this milestone.

## Verification

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_queue_v2_q27_proposal_intelligence.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_queue_v2_q27_proposal_intelligence.py tests/test_queue_v2_q27_proposal_intelligence_verifier.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
.venv/bin/python scripts/verify_documentation_integrity.py
```
