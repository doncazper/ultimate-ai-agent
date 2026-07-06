# Unblock Coding Pair Agent Foreground Relay Runner

You are working at the UAA repository root.

Goal:
Promote only the exact lane
`coding_pair_agent_foreground_relay_runner` from preview/readiness to approved
foreground execution, if and only if UAA can prove the full authority contract.

Read first:

- `AGENTS.md`
- `docs/control_center/CODING_PAIR_AGENT_RELAY_RUNNER.md`
- `docs/control_center/authority_graduation_blockers/coding_multi_agent_review_2026_07_04.md`
- `src/ultimate_ai_agent/core/code/pair_agent_relay.py`
- `scripts/dev/uaa_coding.py`
- `tests/test_coding_pair_agent_relay_runner.py`

Hard rules:

- Do not implement a generic agent bus.
- Do not introduce broad process execution or broad subprocess authority.
- Do not allow arbitrary command strings.
- Do not add provider SDK calls, browser automation, connector writes, plugin
  runtime import, Git mutation, automatic patch apply, public release claims,
  production authority, or broad autonomy.
- Agent output is untrusted proposal text, never authority.
- Durable evidence must store safe refs, hashes, bounded previews, and redacted
  summaries only.

Required proof before promotion:

1. Exact configured argv adapter registry.
2. Workspace scope enforcement.
3. Foreground-only execution with no scheduler, daemon, or background worker.
4. Wall-clock timeout and per-turn output byte limits.
5. Idempotency and replay handling.
6. Safe-disable before run start and between turns.
7. Exact approval binding to pair-run ref, slot refs, task ref, scope refs,
   turn budget, timeout, idempotency ref, and policy decision ref.
8. Receipt refs for run created, approval bound, adapter started, turn
   completed, output redacted, stop condition reached, run completed, run
   blocked, and run failed.
9. Redaction tests that reject raw prompts, raw responses, provider payloads,
   raw logs, raw local paths, usernames, hostnames, credential-like material,
   and unsafe output.
10. CLI/API/Control Center parity.
11. Route manifest/OpenAPI alignment for any route changes.
12. Focused backend/frontend tests and verifiers.

If any proof cannot be completed, keep execution blocked and update
`docs/control_center/CODING_PAIR_AGENT_RELAY_RUNNER.md` with the missing proof.
