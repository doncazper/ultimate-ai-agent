# Phase 04: Action, Tool, Code Lanes, And Approval Receipts

Goal: catch up on operator-visible tool/action/code workflows without granting
broad authority. UAA should have a clear catalog, exact eligibility, proposal
envelopes, approval validation, execution receipts for accepted lanes, and
reviewable code-workbench posture.

## Required Work

1. Inspect UAA's PolicyEngine, LocalApprovalAuthority, Action Inbox, approval
   envelopes, route side-effect classification, provider/tool runtime safety,
   code workbench docs, CLI scripts, and tests.
2. Build or harden a tool/action catalog read model with:
   - capability id;
   - status;
   - side-effect class;
   - required approval scope;
   - eligibility reason;
   - blocked reason;
   - receipt requirements;
   - rollback or safe-disable posture.
3. For any already-approved exact lane, verify:
   - exact approval binding;
   - idempotency;
   - redacted receipt;
   - operator-visible result;
   - CLI/API/Control Center parity;
   - tests and route classification.
4. For code assistance, add or harden proposal-first workflow surfaces:
   - diff/proposal refs;
   - validation plan;
   - test command eligibility;
   - artifact hash/receipt requirements;
   - sandbox/path controls;
   - review and rejection states.
5. Generate unblock prompts for any external-runtime-like execution feature that
   remains blocked.

## Explicit Non-Goals

Do not add unrestricted shell execution, arbitrary command strings, broad tool
invocation, connector writes, browser automation, remote execution, plugin
runtime import, or unapproved code mutation.

Do not let UI controls mint approval, eligibility, authority, or receipts.

## Acceptance Criteria

- Operators can inspect what tools/actions exist and why each is callable,
  approval-required, preview-only, or blocked.
- Approved micro-lanes produce redacted receipts and safe refs.
- Code workflow is reviewable even when execution remains blocked.
- Blocked lanes produce exact future prompts instead of vague TODOs.

## Verification

Run focused policy/action/code-workbench tests plus:

```bash
git diff --check
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
.venv/bin/python scripts/verify_product_truth.py
make frontend-check
```
