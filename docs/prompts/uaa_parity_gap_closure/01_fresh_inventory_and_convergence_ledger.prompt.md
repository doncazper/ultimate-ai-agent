# Phase 01: Fresh Inventory And Convergence Ledger

Objective: establish a current, code-grounded ledger for every H, O, P, B, and
L coverage ID before implementation. Detect work landing from other tasks and
prevent duplicate branches, routes, stores, tests, and UI surfaces.

## Required Work

1. Synchronize with current `origin/main` in a clean orchestration worktree.
2. Record repository SHA, version, branch/worktree state, open PRs, recently
   merged PRs, remote branches, and overlapping local branches.
3. When task inspection tools are available, record active UAA task titles,
   branches, PRs, and owned path groups without steering them.
4. Inspect actual code, tests, API routes, CLI commands, OpenAPI, manifests,
   docs, UI wiring, receipts, evidence, verifiers, benchmarks, and packaging.
5. Classify every ID from the README coverage matrix with one allowed status.
   Use `open_pr_owned_elsewhere` or `in_flight_branch_owned_elsewhere` for
   overlapping work that has not reached `main`; do not count it complete.
6. For every `merged_proven` classification, record concrete code and test refs
   and run the smallest meaningful proof.
7. For every overlap owned elsewhere, record owner/task/branch/PR and exact
   paths. Do not edit those paths until a later inventory shows the work merged
   or abandoned and explicitly handed over.
8. Build a dependency graph and phase execution ledger. Duplicated source IDs
   such as H01/O01/L06 must point to one canonical implementation outcome.
9. Record current live-data versus mock/preview/static posture for each visible
   surface. Do not infer live behavior from route existence.
10. Record authority prerequisites separately from implementation gaps.

Store the ledger under `reports/parity_gap_closure/` using safe refs and no raw
local paths, prompts, payloads, credentials, or logs.

## No-Op And Delta Rules

- Do not change product code in Phase 01 unless a verifier needed to produce
  the inventory is broken; repair it only with focused tests.
- Do not downgrade an implemented capability because its UX could improve;
  record the remaining delta precisely.
- Do not upgrade a capability because a plan, mock, disabled adapter, or open
  PR exists.
- If another task merges during this phase, refresh and reclassify before
  committing.

## Acceptance

- Every H01-H06, O01-O08, P01-P10, B01-B14, and L01-L16 ID appears exactly once
  in the terminal ledger, including canonical aliases.
- Every skip is backed by current-main code, tests, and operator-surface proof.
- Every owned overlap has a non-invasive wait/revisit disposition.
- Phase dependencies, authority prerequisites, and live-data gaps are explicit.
- No competing roadmap is created.

Commit message when the ledger or verifier changes:

```text
docs(parity): establish fresh gap-closure convergence ledger
```
