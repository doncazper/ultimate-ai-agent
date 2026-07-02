# FCC Authority Graduation Program Prompt Bundle

Status: stored execution prompts for the Founder Command Center Authority
Graduation Program. These prompts are operator-run instructions, not runtime
system prompts.

Purpose: Turn read-only/proposal-only work into a gated graduation program for
one exact authority lane at a time without granting broad authority.

## Prompt Order

1. `01_fcc_auth_ramp_charter.prompt.md` - program charter and invariants.
2. `02_read_only_proposal_foundation.prompt.md` - first implementation lane:
   `read_only_real_world_web_fetch` through `WebAccessGateway`.
3. `03_authority_candidate_ranking.prompt.md` - follow-on authority candidate
   scorecard after the fixed WebAccessGateway lane.
4. `04_first_micro_lane_graduation.prompt.md` - follow-on micro-lane
   graduation gate; no substitute lane if prerequisites are missing.

Use `00_execute_all_review_verify_harden.prompt.md` when the operator wants one
end-to-end run through the full program sequence.

## Authority Boundary

The bundle does not grant generic execution, connector writes,
shell/subprocess execution, provider/model authority, memory writes, context
injection, browser automation, remote execution, plugin runtime import,
production-readiness claims, or new route authority by itself.

Only a later accepted micro-lane may add a narrow mutation, and only if it is
exact-scoped, backend-owned, approval-bound, idempotent, auditable,
rollback/safe-disable aware, redacted, CLI/API/core aligned, and verifier-backed.

The first implementation prompt is narrower than the general authority
candidate set. It may only scope `read_only_real_world_web_fetch` through
`WebAccessGateway`: HTTPS GET, explicit allowlist, bounded redacted preview,
durable safe-ref audit, no raw body/header persistence, no browser automation,
no provider SDK calls, no connector writes, no credentials/cookies, no
downloads/uploads, no POST/PUT/PATCH/DELETE, no memory write, no context
injection, no action execution, and no production authority.

## Expected Use

Run the prompts in order. If a later prompt discovers that prerequisites are
missing, it should produce a blocked/no-go receipt and tighten docs/tests rather
than inventing authority.
