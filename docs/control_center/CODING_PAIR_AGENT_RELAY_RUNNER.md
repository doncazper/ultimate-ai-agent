# Coding Pair Agent Relay Runner

Status: preview/readiness only

Canonical lane ref: `coding-pair-agent-lane:coding_pair_agent_foreground_relay_runner`

## Full-Strength Version

UAA Pair Agents should let an operator start a bounded foreground coding relay
between two exact configured agent slots. The useful loop is:

```text
operator task
-> pair-run contract
-> exact configured agent slots
-> approval-bound foreground run
-> UAA-owned relay state
-> bounded turn packets
-> stop on completion, max turns, timeout, user stop, or blocker
-> redacted receipts and evidence refs
-> reviewable Coding or Chat proposal artifact
```

Agent output is untrusted proposal text. It is never approval, truth, patch
authority, Git authority, provider authority, or execution authority.

## Repo-Safe Current Version

The current implementation exposes backend-owned preview/readiness truth only:

- Python Core contract:
  `src/ultimate_ai_agent/core/code/pair_agent_relay.py`
- Coding read route:
  `GET /control-center/coding/multi-agent-review`
- CLI inspection:
  `scripts/dev/uaa_coding.py inspect-pair-agent-relay`
- Additional CLI previews:
  `preview-pair-run`, `inspect-pair-run`, `inspect-pair-artifacts`,
  `inspect-pair-receipts`, `start-pair-run-readiness`, and
  `stop-pair-run-readiness`
- Control Center surface: `/coding` Pair Agents panel

This is not a generic agent bus. The read model records pair-run state,
configured slot refs, argv-template refs, workspace-scope refs, turn limits,
timeout limits, output limits, stop-condition refs, artifact refs, receipt refs,
redaction refs, proof refs, evidence refs, and blocked authority refs.

No foreground adapter process is started. No provider/model call, provider SDK
call, background dispatch, arbitrary command text, unrestricted
shell/subprocess execution, plugin runtime import, browser automation,
connector write, Git mutation, automatic patch apply, raw transcript durable
persistence, public release claim, production authority, or broad autonomy is
added.

## Blocked / Needs Authority

Foreground paired-agent execution remains blocked until UAA proves:

- exact configured argv adapters
- workspace scope enforcement
- foreground-only process policy
- time limits and output limits
- idempotency and replay behavior
- safe-disable before and during a run
- exact LocalApprovalAuthority binding
- redacted receipt and evidence storage
- raw transcript omission by default
- CLI/API/Control Center parity
- route side-effect classification
- focused backend and frontend tests

## Exact Promotion Path

Run the unblock prompt at:

`docs/prompts/authority_graduation_program/generated_unblock_prompts/unblock_coding_pair_agent_foreground_relay_runner.prompt.md`

Promote only the exact named lane
`coding_pair_agent_foreground_relay_runner`. Do not introduce broad process
launching, generic adapter dispatch, provider SDK calls, hidden background
workers, patch apply, Git mutation, browser actions, connector writes, public
release claims, production authority, or broad autonomy.

The first promotable execution slice must still treat every adapter response as
untrusted proposal text and must create redacted receipts with safe refs only.
