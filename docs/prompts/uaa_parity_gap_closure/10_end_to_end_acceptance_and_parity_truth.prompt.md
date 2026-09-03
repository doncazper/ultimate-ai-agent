# Phase 10: End-To-End Acceptance And Parity Truth

Objective: re-inventory the repository after every prior merge, close remaining
in-scope defects, run complete live-data acceptance, and issue a final truthful
verdict without creating another prompt program.

## Final Convergence

1. Sync current `main` and rebuild the complete H/O/P/B/L ledger.
2. Incorporate work that landed from other tasks since Phase 01.
3. Revisit `open_pr_owned_elsewhere`, `in_flight_branch_owned_elsewhere`,
   `blocked_by_external_facility`, and `blocked_by_authority` once.
4. Do not duplicate or seize another active task. If its work merged, verify it;
   if it remains in flight, record the exact remaining dependency.
5. Run at most two focused repair branches/PRs for defects found by final
   acceptance. Merge each only when green.

## Required Live-Data Journeys

Run against a real local Python backend with production frontend code paths:

1. first launch/setup/status/rollback on a supported macOS test environment;
2. Today or Chat to Plan to Action Inbox to Work Board to Evidence to reviewed
   Memory candidate;
3. persistent goal through approval wait, durable events, reconnect, receipt,
   and verified completion;
4. Morning Briefing from real local state and every accepted configured
   read-only source;
5. Work Board concurrent-client conflict and reconciliation;
6. cross-session search with provenance and stale-index handling;
7. backup, verify, fresh-target restore, launch, and state comparison;
8. cancellation, restart, orphan recovery, storage pressure, corrupted evidence,
   and backend-unavailable states; and
9. CLI/API/Control Center equality for every operator-critical state.

No critical journey may rely on production mock data, sample events, placeholder
receipts, hidden manual database edits, or disabled adapters.

## Final Verification

Run focused suites plus:

```bash
git diff --check
.venv/bin/python -m ruff check .
make doctor
make test
make verify
make frontend-check
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py --root .
.venv/bin/python scripts/verify_operational_maturity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
.venv/bin/python -I -B -S scripts/run_foundation_gate.py --command-mode report-only
```

Run applicable visual/browser, packaging, lifecycle, benchmark, backup/restore,
memory, approval, redaction, security, supply-chain, and dogfood checks.

## Truth And Completion Gate

- Every coverage ID has terminal evidence and one allowed classification.
- P0/P1 items cannot remain mock, planned, or undocumented partial while parity
  readiness is claimed.
- `blocked_by_authority` or `blocked_by_external_facility` remains honest and
  prevents the corresponding capability from being called complete.
- Capability, route-status, release-surface, roadmap, product-truth, README, and
  screenshots match observed runtime behavior.
- No public/production/broad-autonomy claim is added without separate evidence.

Create the final redacted report required by Prompt 00. Include exact commits,
PRs, merges, checks, timings, live-data sources, authority decisions, remaining
risks, and clean `main` proof.

Commit message for the final acceptance/truth phase:

```text
test(parity): verify end-to-end live gap closure
```

Stop after the final report and at most two bounded repair passes. Do not
generate follow-up prompts or recursively invoke another pack.
