# FCC Authority Ramp Prompt Bundle

Status: Stored execution prompts for a future Founder Command Center authority
ramp. These prompts are operator-run instructions, not runtime system prompts.

Purpose: Turn read-only/proposal-only work into a gated conveyor for future
micro-lanes without granting broad authority.

## Prompt Order

1. `01_fcc_auth_ramp_charter.prompt.md`
2. `02_read_only_proposal_foundation.prompt.md`
3. `03_authority_candidate_ranking.prompt.md`
4. `04_first_micro_lane_graduation.prompt.md`

Use `00_execute_all_review_verify_harden.prompt.md` when the operator wants one
end-to-end run through the full sequence.

## Authority Boundary

The bundle does not grant generic execution, connector writes,
shell/subprocess execution, provider/model authority, memory writes, context
injection, browser automation, remote execution, plugin runtime import,
production-readiness claims, or new route authority by itself.

Only a later accepted micro-lane may add a narrow mutation, and only if it is
exact-scoped, backend-owned, approval-bound, idempotent, auditable,
rollback/safe-disable aware, redacted, CLI/API/core aligned, and verifier-backed.

## Expected Use

Run the prompts in order. If a later prompt discovers that prerequisites are
missing, it should produce a blocked/no-go receipt and tighten docs/tests rather
than inventing authority.
