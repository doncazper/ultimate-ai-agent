# Phases 10-18: Tools, Memory, Context, And Rollback

These phases borrow Hermes' practical tool, memory, skill, context, and rollback
patterns while keeping UAA review-first and proof-first.

## Shared Acceptance For Phases 10-18

- Durable state lives in Python core.
- Memory, skills, and context never become authority by themselves.
- Skill or memory writes require exact review/approval lanes.
- Context refs use safe refs and sensitive-path blocking.
- Rollback/checkpoint posture is bound to exact mutation lanes.

## Phase 10: Tool Registry With Availability Checks

Branch: `codex/hermes-adoption-10-tool-registry-availability`
Commit: `Add runtime tool registry availability posture`

Full-strength: UAA has an inspectable registry of tools across UAA-native,
Hermes, Codex, Claude, MCP, and future runtimes.

Repo-safe: add read-only tool registry contracts with availability, configured
status, authority class, side-effect class, risk, and blocked reason.

Blocked / needs authority: tool invocation, remote discovery that fetches live
web, plugin import, or connector write activation.

Exact promotion path: per-tool approval, idempotency, safe-disable, rollback
readiness, receipt, proof, and CLI/API tests.

## Phase 11: Bounded Memory Design

Branch: `codex/hermes-adoption-11-bounded-memory`
Commit: `Add bounded governed memory posture`

Full-strength: UAA supports compact durable user/profile/project memory with
quality controls and operator review.

Repo-safe: harden UAA memory read/review models with capacity, target,
staleness, source, why-shown, and rejection/correction posture.

Blocked / needs authority: autonomous memory writes, hidden prompt injection,
external memory provider writes.

Exact promotion path: review queue, approval ref, memory write receipt,
redaction, rollback/supersede, and impact proof.

## Phase 12: Session Search Separate From Memory

Branch: `codex/hermes-adoption-12-session-search`
Commit: `Add session search separate from memory posture`

Full-strength: UAA can search prior sessions and runs without stuffing
everything into durable memory.

Repo-safe: add safe-ref session/run search read models and CLI inspection.

Blocked / needs authority: raw transcript persistence, raw prompt/response
exposure, semantic provider calls, or hidden context injection.

Exact promotion path: redacted indexing, result safe refs, operator-selected
attach flow, retrieval log, and Proof binding.

## Phase 13: Progressive Disclosure Skills

Branch: `codex/hermes-adoption-13-progressive-skills`
Commit: `Add progressive skill disclosure posture`

Full-strength: UAA loads skill metadata first and full instructions only when
approved and relevant.

Repo-safe: align Skill Workbench with compact skill index, safe refs, status,
trust source, review status, and blocked runtime import.

Blocked / needs authority: external code install, plugin runtime import,
marketplace execution, and automatic skill activation.

Exact promotion path: reviewed UAA-owned adaptation, static scan, approval,
quarantine, safe-disable, and receipt.

## Phase 14: Skill Write Approval Gate

Branch: `codex/hermes-adoption-14-skill-write-approval`
Commit: `Add skill write approval gate posture`

Full-strength: agents can propose new or updated skills, and UAA stages them
for operator review before enabling.

Repo-safe: add staged skill-write proposal contracts, diffs, review decisions,
and blocked execution labels.

Blocked / needs authority: agent-authored files landing directly in executable
skill paths.

Exact promotion path: exact LocalApprovalAuthority scope, diff receipt,
quarantine, rollback, static checks, and enablement proof.

## Phase 15: Skill Bundles

Branch: `codex/hermes-adoption-15-skill-bundles`
Commit: `Add skill bundle proposal posture`

Full-strength: UAA supports reusable task profiles combining skills, context,
tools, authority, and verification expectations.

Repo-safe: add bundle metadata/read models and proposal UI. Bundles do not
install, import, or execute skills.

Blocked / needs authority: activating bundles that enable tool execution or
runtime import.

Exact promotion path: bundle review, constituent skill trust, toolset mapping,
approval profile, safe-disable, and tests.

## Phase 16: Context References

Branch: `codex/hermes-adoption-16-context-references`
Commit: `Add governed context reference posture`

Full-strength: UAA supports operator-selected refs like file, folder, diff,
URL evidence, run, proof, task, memory, CRM object, and issue.

Repo-safe: add safe-ref grammar, context preview, budget estimate, why-included,
and blocked URL/live-fetch posture.

Blocked / needs authority: live URL fetch, raw path persistence, automatic
context injection, and secret/config reads.

Exact promotion path: source-specific policy, redaction, preview, approval,
retrieval log, and context-pack receipt.

## Phase 17: Sensitive Path Blocking For Context Refs

Branch: `codex/hermes-adoption-17-sensitive-context-guards`
Commit: `Harden sensitive context reference guards`

Full-strength: UAA blocks secret-bearing and private paths across all context,
file, search, and runtime adapters.

Repo-safe: implement or harden sensitive-ref classification and tests.

Blocked / needs authority: bypass exceptions without explicit operator approval
and proof.

Exact promotion path: narrow allowlist, redacted preview, approval reason,
time-bound grant, receipt, and verifier.

## Phase 18: Checkpoint / Rollback Shadow Store

Branch: `codex/hermes-adoption-18-checkpoint-rollback`
Commit: `Add checkpoint rollback adoption posture`

Full-strength: every mutation lane checkpoints before change and can roll back
by proof ref.

Repo-safe: add or harden checkpoint contracts/read models for exact UAA mutation
lanes. If no mutation lane exists, keep as readiness posture.

Blocked / needs authority: broad filesystem snapshots, rollback execution, or
git mutation outside exact approved lanes.

Exact promotion path: exact workspace scope, checkpoint hash, mutation receipt,
rollback receipt, idempotency, and CLI/API/UI parity.

