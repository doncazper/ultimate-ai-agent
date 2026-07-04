# Coding Multi-Agent Review Authority Blocker

Date: 2026-07-04

Lane: Coding Cockpit Prompt 08 Multi-Agent Review

## Full-Strength Version

UAA Coding Cockpit should coordinate Codex implementer, Claude reviewer, local
verifier, security reviewer, UX reviewer, test fixer, and merge captain
workflows with comparable plans, reviews, diffs, disagreements, handoffs,
receipts, and Proof Detail links.

## Repo-Safe Current Version

`GET /control-center/coding/multi-agent-review` and
`scripts/dev/uaa_coding.py inspect-multi-agent-review` expose backend-owned
safe refs only. The model records agent slot refs, plan refs, review refs,
diff-comparison refs, disagreement refs, handoff refs, proof refs, blocker
refs, redaction refs, and promotion-path refs.

No provider/model call, provider SDK call, local agent execution, multi-agent
dispatch, background autonomy, context injection, shell/subprocess execution,
file write, Git mutation, browser automation, connector write, artifact body
storage, receipt creation, or Proof Detail binding is enabled by this lane.

## Blocked / Needs Authority

- Provider/model calls and provider SDK calls.
- Local agent execution and multi-agent dispatch.
- Background agents, schedulers, and autonomous execution.
- Runtime context injection.
- Raw prompt, raw response, and provider payload persistence.
- Artifact body storage for agent plans, reviews, comparisons, disagreements,
  and handoffs.
- Receipt creation and Proof Detail binding.
- Shell/subprocess execution and allowlisted verifier execution.
- File writes, patch application, Git mutation, browser automation, connector
  writes, and production authority.

## Exact Promotion Path

Promote only after UAA has:

- exact scope for each agent slot and artifact kind
- redaction rules for prompts, responses, provider payloads, raw paths, diffs,
  logs, and private data
- LocalApprovalAuthority binding wherever runtime calls or local verifier
  execution are introduced
- safe-disable posture
- idempotency and retry posture
- receipt and Proof Detail contracts
- CLI parity
- frontend truth labels
- focused backend/frontend tests and verifiers

Until then, Trust and `/coding` must keep multi-agent execution, artifact body
storage, receipts, and Proof Detail binding blocked.
