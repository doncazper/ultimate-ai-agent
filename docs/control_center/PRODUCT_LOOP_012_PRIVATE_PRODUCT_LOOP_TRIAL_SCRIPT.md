# Product Loop 012 Private Product Loop Trial Script

Status: implemented as a local/private, safe-ref-only manual trial artifact.

Product Loop 012 adds a repeatable Private product loop trial script for Boot,
Today, Morning Briefing, Follow-Ups, Memory, Actions, Plans, Chat Handoff,
Evidence, Weekly Review, and Settings. The script is a manual operator review
checklist plus an acceptance ledger scaffold; it does not add backend routes,
runtime authority, provider/model calls, connector runtime, live web,
shell/browser execution, telemetry export, public beta, public distribution,
production readiness claims, or production authority.

## Contract

- Contract ref:
  `contract-ref:product-loop-012-private-product-loop-trial-script:v1`
- Builder:
  `ultimate_ai_agent.core.readiness.build_private_product_loop_trial_script`
- Artifact:
  `docs/control_center/private_product_loop_trial_script_v1.json`
- CLI inspection:
  `scripts/inspect_product_loop_trial_script.py` (human checklist by default,
  machine JSON only with `--json`)
- Verifier:
  `scripts/verify_product_loop_012_private_trial_script.py`
- Focused tests:
  `tests/test_product_loop_012_private_trial_script.py`

## Manual Trial Surfaces

The required surfaces are Boot, Today, Morning Briefing, Follow-Ups, Memory,
Actions, Plans, Chat Handoff, Evidence, Weekly Review, and Settings. Each
surface has a manual step ref, safe evidence refs, acceptance ledger refs,
blocked state refs, and a next safe action. Findings remain
`pending_operator_review` until a human records a later safe gap report.

## Safety Boundary

The Product Loop 012 script is local/private and safe-ref-only. It requires
manual operator review and keeps all authority denied: no public beta, no
public distribution, no telemetry export, no connector runtime, no connector
writes, no connector reads, no provider/model calls, no provider SDK calls, no
live web, no shell/browser execution, no action execution, no memory writes, no
backend route, no runtime authority, no production readiness claims, and no
production authority.

The artifact must not store raw prompt content, raw response content, provider
payload content, private paths, logs, usernames, hostnames, credentials,
secrets, or other raw/private material. Use safe refs and redacted summaries
only.

## Acceptance Ledger

The acceptance ledger is a posture scaffold, not an acceptance claim. Each row
links a surface to an acceptance question ref, an expected gap report ref, and
manual-review evidence refs. The default review state is
`pending_operator_review`; accepted or revised findings are intentionally out
of scope for this PR.

## Final Report Template

After running the script, the operator should produce a Product Loop Completion
Report with completed task refs, verification refs, skipped check refs,
product gaps, UX gaps, safety gaps, platform gaps, runtime gaps, and recommended
next roadmap lanes. The report remains local/private and evidence-backed.
