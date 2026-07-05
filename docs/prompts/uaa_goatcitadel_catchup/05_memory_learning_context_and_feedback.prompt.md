# Phase 05: Memory, Learning, Context, And Feedback

Goal: make UAA's memory and learning posture more GoatCitadel-competitive:
explicit intake, review, feedback, correction, provenance, quality controls,
staleness handling, and memory-to-loop binding.

This phase must keep memory as recall and reviewable context, not truth or
authority.

## Required Work

1. Inspect UAA memory docs, memory workbench, ranked retrieval, provenance,
   review decisions, cross-surface intake, memory-to-loop binding, API routes,
   CLI scripts, and tests.
2. Define or harden memory lifecycle states:
   - proposed;
   - active;
   - needs review;
   - corrected;
   - rejected;
   - stale;
   - forgotten;
   - blocked.
3. Add explicit feedback and correction flows where they can be local,
   approval-bound if mutating, redacted, and testable.
4. Bind memory proposals to the productized agent loop:
   - what evidence produced the proposal;
   - why it may help future work;
   - who reviewed it;
   - whether it is accepted, corrected, rejected, or stale.
5. Add or improve context-pack generation and inspection without giving memory
   automatic instruction or authority status.
6. Add quality controls:
   - dedupe;
   - source/provenance;
   - confidence or quality labels;
   - staleness;
   - conflict handling;
   - safe refs/redaction.

## Safe Implementation Shape

- Proposal-first memory intake is preferred.
- Memory writes require an exact existing approved lane or remain blocked.
- Context packs must separate facts, assumptions, memories, and unknowns.
- Retrieved memory cannot authorize actions, override policy, or change route
  side-effect class.

## Acceptance Criteria

- Operators can review, accept, correct, reject, forget, and inspect provenance
  for memory items where exact lanes exist.
- Blocked memory writes are clearly blocked, not hidden behind UI affordances.
- Memory-to-action binding is visible but not authoritative.
- Tests cover staleness, correction/rejection, provenance, and redaction.

## Verification

Run focused memory tests plus:

```bash
git diff --check
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
make frontend-check
```
