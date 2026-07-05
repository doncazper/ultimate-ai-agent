# Phase 06: Evidence, Audit, Receipts, And Observability

Goal: make UAA's proof surfaces more operator-visible and tamper-aware:
timeline, receipts, provenance, redaction, runtime state, and offline
inspection where practical.

## Required Work

1. Inspect UAA evidence timeline, event log, receipt viewer, audit docs,
   storage, run/receipt trace viewer, release evidence, redaction utilities,
   API routes, CLI scripts, and tests.
2. Define or harden a common receipt envelope for agent-loop events:
   - receipt id and safe refs;
   - run/action/approval ids;
   - side-effect class;
   - authority decision;
   - inputs as safe refs or redacted summaries;
   - outputs as safe refs or redacted summaries;
   - artifact hash refs when applicable;
   - timestamp;
   - verifier version;
   - redaction status.
3. Add operator-facing evidence timeline grouping:
   - plan changes;
   - approval waits;
   - action proposals;
   - execution receipts for accepted lanes;
   - memory proposals and review decisions;
   - blocked/no-go events;
   - recovery events.
4. Add CLI/API inspection for receipt and timeline queries.
5. Add tests and verifiers for redaction, receipt schema, evidence refs,
   missing receipt handling, and no raw payload persistence.

## Safe Implementation Shape

- Safe refs and bounded summaries only.
- Do not persist raw prompt content, raw model responses, provider payloads,
  local absolute paths, logs, credentials, tokens, cookies, hostnames, or
  environment dumps.
- Evidence is proof of what UAA did or refused; it is not new authority.

## Acceptance Criteria

- Operators can answer: what happened, who approved it, what policy allowed or
  blocked it, what evidence exists, and what remains unknown.
- Receipt/timeline surfaces degrade safely when evidence is missing.
- Tests fail on raw-payload and unsafe-path leaks in new surfaces.
- UI avoids raw JSON for critical evidence workflows.

## Verification

Run focused evidence/redaction tests plus:

```bash
git diff --check
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
make frontend-check
```
