# Coding Pair Agent Relay Runner Prompt Pack

Status: stored execution prompts, not runtime authority

Purpose: graduate UAA's Coding Cockpit multi-agent review idea from a blocked
read model toward a bounded foreground paired-agent relay runner. The target is
to let two configured coding agents iterate on a task through UAA-owned relay
state while UAA enforces scope, turn budget, stop controls, approvals,
redaction, receipts, and operator visibility.

Canonical lane name: Foreground Paired Agent Relay Runner.

Safety summary: agent output is untrusted proposal text; no arbitrary command strings are allowed.

This pack is deliberately not a generic agent bus. It does not grant provider
SDK calls, unrestricted shell/subprocess execution, background autonomy, browser
automation, connector writes, Git mutation, automatic patch apply, production
authority, or broad local-agent execution by itself.

## Product Shape

```text
operator task
-> pair-run contract
-> exact configured agent slots
-> approval-bound foreground run
-> UAA-owned relay state
-> bounded agent turn packets
-> stop on completion, max turns, timeout, user stop, or blocker
-> redacted receipts/evidence
-> reviewable Coding/Chat proposal artifact
```

## Wrapper Command

```bash
bash scripts/dev/run_coding_pair_agent_relay_runner_prompt_pack.sh
```

Dry-run:

```bash
bash scripts/dev/run_coding_pair_agent_relay_runner_prompt_pack.sh --dry-run
```

Emit combined prompt:

```bash
bash scripts/dev/run_coding_pair_agent_relay_runner_prompt_pack.sh --dry-run --output /tmp/coding-pair-agent-relay-runner.md
```

## Prompt Order

1. `00_execute_coding_pair_agent_relay_runner_end_to_end.prompt.md`
2. `01_baseline_authority_and_product_truth.prompt.md`
3. `02_pair_run_contracts_and_state_machine.prompt.md`
4. `03_adapter_registry_policy_and_approval_gate.prompt.md`
5. `04_foreground_relay_runner_orchestrator.prompt.md`
6. `05_transcript_artifacts_receipts_and_evidence.prompt.md`
7. `06_coding_chat_cli_api_ui_surfaces.prompt.md`
8. `07_final_hardening_and_graduation_truth.prompt.md`

## Fail-Closed Rule

If existing UAA authority cannot safely support foreground agent adapter
execution, implement the preview/contracts/readiness lane and generate an exact
unblock prompt. Do not add broad process launching, hidden provider calls, or
background agent dispatch to make the demo work.

## Verification

```bash
.venv/bin/python scripts/verify_coding_pair_agent_relay_runner_prompt_pack.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_coding_pair_agent_relay_runner_prompt_pack.py -q
```

