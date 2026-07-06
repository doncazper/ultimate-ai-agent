# Coding Pair Agent Relay Runner Authority Blocker

Date: 2026-07-06

Lane: `coding_pair_agent_foreground_relay_runner`

## Full-Strength Version

UAA Coding Pair Agents should run two exact configured coding-agent slots in a
bounded foreground relay. The operator task becomes a pair-run contract, the
contract binds agent slots, workspace scope, turn budget, timeout, output
limits, approval refs, stop conditions, receipt refs, evidence refs, and Proof
refs, and each adapter response remains untrusted proposal text for operator
review.

## Repo-Safe Current Version

The current lane is backend-owned preview/readiness only. Python Core exposes
the read model through the existing Coding multi-agent review route and
inspection CLI:

- `GET /control-center/coding/multi-agent-review`
- `scripts/dev/uaa_coding.py inspect-pair-agent-relay`
- `scripts/dev/uaa_coding.py preview-pair-run`
- `scripts/dev/uaa_coding.py inspect-pair-run`
- `scripts/dev/uaa_coding.py inspect-pair-artifacts`
- `scripts/dev/uaa_coding.py inspect-pair-receipts`
- `scripts/dev/uaa_coding.py start-pair-run-readiness`
- `scripts/dev/uaa_coding.py stop-pair-run-readiness`

The Control Center `/coding` Pair Agents panel renders only safe refs, blocked
state, bounded turn/time/output posture, artifact refs, receipt refs, proof
refs, evidence refs, and the future unblock prompt ref.

No foreground adapter process is started. No generic agent bus, provider SDK
call, provider/model call, background dispatch, arbitrary command text,
unrestricted shell/subprocess execution, plugin runtime import, browser
automation, connector write, Git mutation, automatic patch apply, raw
transcript persistence, production authority, public release claim, or broad
autonomy is added.

## Blocked / Needs Authority

- Exact configured argv adapter registry.
- Workspace scope enforcement for every adapter run.
- Foreground-only process supervision with no scheduler or hidden worker.
- Wall-clock timeout, per-turn output limit, and max-turn enforcement.
- Idempotency and replay behavior.
- Safe-disable before run start and between turns.
- Exact LocalApprovalAuthority binding to the pair-run ref, slot refs, task
  ref, scope refs, turn budget, timeout, idempotency ref, and policy decision.
- Redacted receipts for run-created, approval-bound, adapter-started,
  turn-completed, output-redacted, stop-condition-reached, run-completed,
  run-blocked, and run-failed.
- Raw transcript, raw prompt, raw response, provider payload, raw log, raw
  local path, username, hostname, credential-like, and secret-like leakage
  rejection.
- CLI/API/Control Center parity for every operator-relevant state.
- Route classification and OpenAPI/manifest alignment if an execution route is
  added.

## Exact Promotion Path

Use:

`docs/prompts/authority_graduation_program/generated_unblock_prompts/unblock_coding_pair_agent_foreground_relay_runner.prompt.md`

Promote only the named lane. Do not broaden it into generic subprocess,
generic adapter dispatch, provider SDK usage, hidden background agents,
automatic patch apply, Git mutation, connector writes, browser automation,
production authority, or broad autonomy.
