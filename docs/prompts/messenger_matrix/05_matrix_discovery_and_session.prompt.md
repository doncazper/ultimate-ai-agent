# MSG-MX-005 — Matrix Discovery And Governed Session

Implement only Phase 4 of the Messenger Matrix plan. Read `AGENTS.md`, the full
design sources, accepted authority matrix, provider/network boundaries,
credential-vault contracts, capability availability, policy/approval/lease
contracts, and session security tests before editing.

## Branch Contract

- Fetch current `origin/main`, record its SHA, and create
  `codex/msg-mx-05-discovery-session` from that exact commit in an isolated
  worktree.
- Inspect overlapping provider/session work and preserve unrelated changes.
  Never reset, revert, clean, stash, overwrite, force-push, or move tags.
- Prove MSG-MX-004 is merged and post-merge verified on the current
  `origin/main`; otherwise stop with an explicit blocked report.

Python Core remains authoritative and Control Center remains an operator shell.
Preserve API/CLI parity for every session posture and exact command.

## Stage A — Exact Authority Acceptance

On this branch and PR, first implement and verify separately scoped lanes for
Matrix discovery/network access, connector session creation, account
authentication, macOS credential storage, system-browser SSO launch, and the
allowlisted loopback callback/redirect. Bind each to exact homeserver, account,
adapter, endpoint class, redirect target, credential backend, TTL, deadline,
budget, target validation, kill switch, safe-disable, readiness, idempotency,
rollback/revocation, redaction, and content-free receipts. Add adversarial tests
for SSRF, redirect substitution, callback replay, credential fallback, approval-
ref misuse, stale leases, and duplicate session ownership.

Review and verify Stage A locally before Stage B. Acceptance makes each lane
eligible for fresh request-scoped evaluation only; it does not grant standing
authority, authenticate an account, or make UI state callable. If exact
authority cannot be safely accepted, stop before Stage B with an explicit
blocked report.

Immediately before every Stage B runtime call, including discovery,
capability reads, authentication, session refresh, logout, and revocation,
re-evaluate PolicyEngine; exact LocalApprovalAuthority scope where required;
the current exact AuthorityLease; exact capability, adapter, provider, target,
mission, and run; TTL/deadline; budget; readiness; kill switch; safe-disable;
and idempotency/replay posture. Approval refs alone never authorize. Unknown,
stale, expired, or mismatched state fails closed before the call starts.

## Stage B — Runtime Implementation

Implement:

- inspect the current stable `matrix-js-sdk` release and its compatibility
  guidance, then install one exact version with the repository package manager
  and commit the resulting lockfile; no range, preview, beta, RC, or nightly;
- account for the exact Rust/WASM crypto dependency and assets required by that
  SDK version, document bundler/CSP/loading constraints, add dependency-license
  and SBOM coverage, and fail closed when required assets are missing;
- keep every Matrix SDK import inside the approved adapter boundary and add a
  static guardrail test that rejects imports from UI or unrelated core modules;

- `/.well-known/matrix/client`, supported-version, legacy login-flow, and current
  OAuth metadata discovery through the approved adapter boundary;
- capability reporting before connection;
- supported password and browser SSO/OAuth selection only when advertised;
- macOS credential-backed access/refresh tokens, stable device ID, singleton
  client/crypto-store lifecycle lock, refresh, soft logout, logout, and revoke;
- safe failure handling for bad discovery, unsupported auth, rate limits,
  credential failure, revocation, and duplicate lifecycle ownership.

Document and test dependency rollback: safe-disable the adapter, revoke the
session, remove or restore the exact pin and lockfile atomically, and preserve
content-free failure receipts. Do not upgrade unrelated dependencies.

Raw token import remains blocked. Tokens must use authorization headers and must
never enter URLs, logs, receipts, fixtures, API responses, or durable prompts.
No sync, room read, message send, or room mutation is in scope.

Every session mutation requires exact safe refs, redaction, idempotency, content-
free receipts, rollback/revocation, and safe-disable. Re-evaluate PolicyEngine,
exact LocalApprovalAuthority scope, the current exact AuthorityLease, adapter,
target, TTL/deadline, budget, readiness, kill switch, and idempotency/replay
immediately before execution.

## Required Verification

Run focused discovery/session/credential/redaction/authority/CLI/API tests and
bounded local-harness integration tests, then:

```bash
.venv/bin/python -m ruff check .
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py tests/test_control_center_api_routes.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_frontend.py
make frontend-check
PYTHONPATH=src .venv/bin/python scripts/run_foundation_gate.py --command-mode report-only --no-write-latest
git diff --check
```

Adversarially review SSRF/discovery redirects, token leakage, credential fallback,
session duplication, stale capability truth, revocation races, and authority
bypass, dependency drift, license gaps, unsafe SDK imports, and missing WASM
assets. Fix all actionable findings. Commit and push normally and open a draft
PR. While it is draft, complete local review and hardening of both stages. Mark
it ready only after local checks pass; run only repository-scoped self-hosted
macOS CI, never paid or GitHub-hosted compute. Merge only when required checks
are green, update local `main` to the exact remote merge, run post-merge
verification, push verified `main`, and confirm a clean worktree. Do not begin
MSG-MX-006 before that proof.
The post-merge push must be a synchronization no-op: local `main` and
`origin/main` must resolve to the exact same merge SHA. If verification finds a
defect or divergence, use a new scoped branch and PR; never repair `main`
directly.

This milestone is desktop-only. Do not add, test, capture, or claim mobile
surfaces.

Final report: accepted authority refs, endpoints/flows implemented, denied flows,
tests, blockers, commit, pushed branch, and draft PR URL.
