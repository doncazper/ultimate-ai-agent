# Governed Runtime Pilot Prompt Pack

Status: stored execution prompts, not runtime authority

Purpose: promote UAA from governing blocked authority to governing real local
runtime authority. This pack is intentionally larger than a micro-lane. It
creates a `v0.105.0` governed runtime pilot that can call a configured local
model endpoint, request exact approval, execute allowlisted local commands, and
store redacted runtime evidence with CLI and Control Center parity.

The pack does not grant authority by existing in the repository. Authority is
granted only when an operator executes the prompts, updates the project
contract, implements the runtime gates, verifies the behavior, commits, merges,
tags, and pushes the accepted milestone.

## Wrapper Prompt

Run:

```text
docs/prompts/governed_runtime_pilot/00_execute_end_to_end_merge_push_harden.prompt.md
```

The wrapper executes every phase in order. After each implementation phase it
requires review, hardening, focused verification, commit, push, PR creation,
merge commit to `main` only when green, and a fresh pull before continuing.

## Prompt Order

1. `00_execute_end_to_end_merge_push_harden.prompt.md`
2. `01_baseline_freeze_and_runtime_milestone.prompt.md`
3. `02_runtime_contracts_profiles_and_manifest.prompt.md`
4. `03_local_model_runtime_gateway.prompt.md`
5. `04_governed_command_runtime.prompt.md`
6. `05_action_inbox_execution_bridge.prompt.md`
7. `06_control_center_cli_evidence_runtime_ux.prompt.md`
8. `07_review_fix_harden_release_truth.prompt.md`

## Target Runtime Promotion

- `sealed`: current default posture. No runtime model/tool execution.
- `local-runtime`: configured loopback/local model calls and allowlisted local
  command execution are available behind runtime policy.
- `operator-approved`: runtime actions require exact Action Inbox approval
  envelopes before execution.

## Included Authority

- Local OpenAI-compatible loopback model calls through one runtime gateway.
- Governed command execution for allowlisted argv-only commands.
- Approval-backed Action Inbox execution for exact pending runtime actions.
- Runtime invocation receipts, policy decisions, evidence refs, and rollback or
  safe-disable records.
- CLI/API/Control Center parity for status, pending approvals, execution, and
  receipts.

## Explicit Non-Goals

- No browser automation.
- No browser observe or browser action.
- No connector reads or writes.
- No unrestricted web fetch.
- No provider SDK sprawl or remote provider authority.
- No plugin runtime import.
- No remote execution.
- No production authority, public beta, public release, or broad autonomy.
- No raw prompt, response, provider payload, log, local path, username,
  hostname, environment dump, credential, or secret-like value in durable
  evidence.

## Success Shape

The first useful loop is:

1. Operator opens Chat.
2. UAA calls a configured local model through `RuntimeGateway`.
3. Model output is treated as untrusted proposal text.
4. UAA creates an Action Inbox item for an exact runtime action.
5. Operator approves the exact envelope.
6. UAA executes the allowlisted command through governed runtime.
7. Output is redacted, bounded, and stored as safe evidence.
8. Control Center and CLI show the same receipt and policy decision.
