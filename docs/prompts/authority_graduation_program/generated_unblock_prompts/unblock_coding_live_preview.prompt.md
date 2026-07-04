# Unblock Coding Live Preview

You are working in the UAA repository.

Goal:
Graduate the Coding Cockpit live preview lane from read-only readiness refs to
the smallest safe runtime preview capability.

Read first:

- `AGENTS.md`
- `docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md`
- `docs/control_center/authority_graduation_blockers/coding_live_preview_2026_07_04.md`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`

Hard rules:

- Python Agent Core owns durable product truth.
- Control Center is presentation/initiation only.
- Do not add broad shell/subprocess execution.
- Do not start or stop dev servers unless the exact lane grants it.
- Do not automate browser clicks, forms, auth, cookies, downloads, or uploads.
- Do not persist raw URLs, raw console output, screenshots containing private
  data, raw paths, credentials, tokens, or private data.
- Do not claim production readiness or public distribution.

Required design:

1. Define the exact full-strength goal, repo-safe scope, blocked authority, and
   promotion path.
2. Add backend-owned contracts for dev-server status, preview URL refs,
   screenshot artifact refs, console summaries, visual proof refs, route
   checklist refs, viewport refs, receipt refs, and Proof Detail refs.
3. Bind every runtime observation to explicit authority mode, approval posture,
   redaction, safe-disable, idempotency, receipt, rollback/checkpoint posture
   where applicable, and CLI parity.
4. Keep browser interaction and dev-server lifecycle control blocked unless
   separately scoped.
5. Add focused backend tests, frontend tests, docs, route manifests, OpenAPI
   updates, product-truth checks, and operational-maturity checks.

Acceptance:

- The lane remains fail-closed by default.
- Any enabled preview capability is exact-scoped and receipt/proof-backed.
- `/coding`, Trust, docs, and CLI all show the same enabled and blocked state.
- No broad runtime, browser, shell, provider/model, connector, Git, file-write,
  public release, or production authority is added.
