# Unblock Coding Approved Patch Apply

Goal:
Implement exactly one approved Coding Cockpit patch apply lane with checkpoint,
receipt, rollback posture, redaction, CLI parity, and Proof Detail binding.

Branch:
`codex/unblock-coding-approved-patch-apply`

Read first:

- `AGENTS.md`
- `docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md`
- `docs/control_center/authority_graduation_blockers/coding_approved_patch_apply_2026_07_04.md`
- `src/ultimate_ai_agent/core/code/coding_cockpit.py`
- `src/ultimate_ai_agent/core/files/manager.py`
- `src/ultimate_ai_agent/core/files/operations.py`

Hard rules:

- Do not broaden authority beyond exact approved Coding patch apply.
- Do not add arbitrary file writes, shell/subprocess execution, Git mutation,
  provider/model calls, browser automation, connector writes, background
  autonomy, public release, or production authority.
- Do not persist raw prompt, response, provider payload, raw local path, raw
  file content, credential material, account data, command output, or private
  data.
- Python Agent Core owns durable truth.
- Control Center only renders backend-owned state and initiates exact approved
  requests.

Implementation scope:

1. Add exact patch artifact storage over safe refs only.
2. Add selected file or hunk scope contract.
3. Add LocalApprovalAuthority validation for selected proposal, authority mode,
   session, and workspace refs.
4. Add checkpoint creation before apply.
5. Add apply receipt with safe preimage, postimage, rollback, evidence, and
   proof refs.
6. Add rollback posture and receipt inspection.
7. Add sensitive diff guard for protected values, generated output, deletes, and
   sensitive config.
8. Add CLI inspection for apply readiness, apply receipt, and rollback posture.
9. Add frontend controls only when backend read models prove exact authority.
10. Update route status, release surface, OpenAPI/API manifest tests, docs, and
    verifiers.

Acceptance:

- Patch apply is real only for the exact selected approved proposal.
- Receipt proves what changed using safe refs only.
- Rollback posture is available and exact-scoped.
- Mock fallback and missing backend state cannot expose mutation controls.
- All broad runtime authority remains blocked.
- Focused tests and required verifiers are green.
