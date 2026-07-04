# Unblock Coding Multi-Agent Review

You are working in the UAA repository.

Goal:
Graduate the Coding Cockpit multi-agent review lane from read-only readiness
refs to the smallest safe reviewed artifact capability.

Read first:

- `AGENTS.md`
- `docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md`
- `docs/control_center/authority_graduation_blockers/coding_multi_agent_review_2026_07_04.md`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`

Hard rules:

- Python Agent Core owns durable product truth.
- Control Center is presentation/initiation only.
- Do not add broad provider/model, local agent, shell/subprocess, file-write,
  Git, browser, connector, background autonomy, public release, or production
  authority.
- Do not persist raw prompts, raw responses, provider payloads, raw paths, raw
  file content, raw diffs, raw logs, credentials, tokens, or private data.
- Do not dispatch Codex, Claude, local agents, reviewers, verifiers, test
  fixers, or merge workflows unless this PR explicitly scopes and tests the
  exact authority lane.

Required design:

1. Define the exact full-strength goal, repo-safe scope, blocked authority, and
   promotion path.
2. Add backend-owned reviewed-artifact contracts for multi-agent plan, review,
   comparison, disagreement, and handoff outputs using safe refs and bounded
   redacted summaries only.
3. Bind every runtime call or local verifier execution to exact authority mode,
   approval posture, redaction, safe-disable, idempotency, receipt, proof, and
   CLI parity.
4. Keep provider/model calls, provider SDK calls, local agent execution,
   background dispatch, context injection, artifact body storage, shell,
   file-write, Git, browser, connector, and production lanes blocked unless
   separately scoped.
5. Add focused backend tests, frontend tests, docs, route manifests, OpenAPI
   updates, product-truth checks, and operational-maturity checks.

Acceptance:

- The lane remains fail-closed by default.
- Any enabled reviewed artifact is exact-scoped and receipt/proof-backed.
- `/coding`, Trust, docs, and CLI all show the same enabled and blocked state.
- No broad runtime, browser, shell, provider/model, connector, Git, file-write,
  public release, or production authority is added.
