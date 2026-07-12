# Phase 08: macOS Cockpit And CLI/API Parity

Goal: present one backend-owned operator truth across the macOS-first Control
Center, human-readable CLI, API/OpenAPI, manifests, and route inventory.

## Required Work

1. Inspect existing Control Center navigation/components, Python read models,
   CLI commands, API client/routes, OpenAPI, `/api/manifest`, route side-effect
   classification, SSE preview, product language, and visual manifests.
2. Show operator-readable posture for:
   - intent, confidence, ambiguity, and unknowns;
   - plans, dependencies, mission progress, workers, and heartbeat state;
   - approval waits, retries, dead letters, and cancellation;
   - mission budgets, reservations, settlements, and unresolved cost;
   - adapters, providers, SearXNG/Firecrawl citations, and untrusted evidence;
   - memory review and context manifests;
   - active leases, expiry, kill switch, and safe-disable; and
   - receipts, evidence, rollback posture, and blocked reasons.
3. Human-readable CLI is primary; JSON is optional and redacted. Every mutation
   maps to the same Python contract and cannot bypass policy, approval, lease,
   budget, kill switch, safe-disable, idempotency, or rate limits.
4. Keep stable unique OpenAPI operation IDs, exact route classification,
   protected local auth, and `/api/manifest` as stable declaration metadata,
   not a live health dashboard.
5. Remove fake, misleading, or unwired controls. Product truth must not live in
   React state and raw JSON must not be the primary operator workflow.
6. Preserve bounded deterministic SSE progress-preview replay as replay, not
   live streaming.

## Platform Boundary

macOS is canonical. Linux and Windows remain explicit render placeholders
derived from the current macOS product until beta/port work is separately
authorized. Do not implement or claim those platforms in this phase.

## Required Proofs

- API/CLI/UI render the same backend-owned refs and states;
- Control Center cannot mint authority;
- blocked/degraded/unknown states are readable;
- web evidence is visibly untrusted and cited;
- exact lease, expiry, budget, kill switch, and receipts are visible;
- route auth/classification/OpenAPI/manifest contracts agree; and
- no raw prompt, response, payload, log, path, or secret leaks.

## Verification

Run focused backend/frontend tests, typecheck, lint, production build, focused
Playwright/browser checks, product-language and visual-regression verification,
OpenAPI/route/API-manifest gates, docs/redaction checks, Foundation Gate
report-only with `--no-write-latest`, and `git diff --check`.

## Exit

The macOS cockpit, CLI, and API present one readable governed truth. Other
platforms remain explicit placeholders.
