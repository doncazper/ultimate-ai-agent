# Unblock Coding Allowlisted Test Command

Goal:
Implement exactly one allowlisted Coding Cockpit test command lane with command
preview, timeout policy, bounded redacted output summary, exit status, receipts,
CLI parity, and Proof Detail binding.

Branch:
`codex/unblock-coding-allowlisted-test-command`

Read first:

- `AGENTS.md`
- `docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md`
- `docs/control_center/authority_graduation_blockers/coding_allowlisted_test_command_2026_07_04.md`
- `src/ultimate_ai_agent/core/code/coding_cockpit.py`
- `src/ultimate_ai_agent/core/execution/durable_runs.py`
- `src/ultimate_ai_agent/core/execution/run_storage.py`

Hard rules:

- Do not broaden authority beyond exact allowlisted Coding test commands.
- Do not add arbitrary shell execution, installs, network commands, destructive
  commands, background processes, Git mutation, provider/model calls, browser
  automation, connector writes, public release, or production authority.
- Do not persist raw prompt, response, provider payload, raw local path, raw
  command, raw command output, credential material, account data, environment
  dumps, or private data.
- Python Agent Core owns durable truth.
- Control Center only renders backend-owned state and initiates exact approved
  requests.

Implementation scope:

1. Add an exact command allowlist for focused pytest, frontend test,
   lint/typecheck, and repo verifier refs.
2. Add command preview contracts with bounded arguments and denied command
   classes.
3. Add LocalApprovalAuthority validation where the selected command requires
   explicit approval.
4. Add timeout and termination posture.
5. Add bounded output redaction and summary storage.
6. Add exit-code/status capture.
7. Add command and test receipts with evidence and proof refs.
8. Add safe-disable posture and idempotency refs.
9. Add CLI inspection for readiness, command receipt, test receipt, and blocked
   posture.
10. Add frontend controls only when backend read models prove exact authority.
11. Update route status, release surface, OpenAPI/API manifest tests, docs, and
    verifiers.

Acceptance:

- Only exact allowlisted commands can run.
- Denied command classes remain blocked: arbitrary shell, installs, network
  commands, destructive commands, and background processes.
- Receipts prove status using safe refs and bounded redacted summaries only.
- Mock fallback and missing backend state cannot expose execution controls.
- All broad runtime authority remains blocked.
- Focused tests and required verifiers are green.
