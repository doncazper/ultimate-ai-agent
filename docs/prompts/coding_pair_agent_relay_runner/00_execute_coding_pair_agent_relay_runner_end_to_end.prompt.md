# Execute CODING-PAIR-AGENT-RELAY-RUNNER-001 End To End

Role: Principal agent runtime architect, coding cockpit product engineer,
security reviewer, implementation lead, and adversarial hardening reviewer for
UAA.

Goal: build the UAA-native path from blocked Coding Cockpit multi-agent review
readiness toward a bounded foreground paired-agent relay runner. The useful
target is two configured coding agents iterating through UAA-owned relay state,
with turn budget, stop controls, approvals, receipts, redacted evidence, and
operator-visible artifacts.

## Read First

- `AGENTS.md`
- `README.md`
- `VERSION.md`
- `SECURITY.md`
- `docs/prompts/coding_pair_agent_relay_runner/README.md`
- every prompt in `docs/prompts/coding_pair_agent_relay_runner/`
- `docs/control_center/authority_graduation_blockers/coding_multi_agent_review_2026_07_04.md`
- `docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
- `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
- `docs/architecture/TURN_CONTRACT_ROUTER.md`
- `docs/api/openapi_contract.md`
- `docs/api/route_inventory.md`

Inspect existing code before editing:

```bash
pwd
git status --short --branch
git branch --show-current
git rev-parse HEAD
rg "multi-agent|agent review|CodingMultiAgentReview|RuntimeGateway|approval|subprocess|command|receipt|evidence|idempotency|safe-disable" src tests apps docs scripts
```

## Global Rules

- Treat `AGENTS.md` as binding.
- Preserve unrelated dirty files and user changes.
- Do not implement a generic agent bus.
- Do not add provider SDK calls, browser automation, connector writes,
  unrestricted shell/subprocess execution, plugin runtime import, Git mutation,
  automatic patch apply, public release claims, production authority, or broad
  autonomy.
- If local agent process execution is promoted, it must be a named exact lane:
  `coding_pair_agent_foreground_relay_runner`.
- Foreground adapter execution is allowed only if existing UAA governed runtime
  and approval infrastructure can enforce exact configured argv adapters,
  workspace scope, time limits, output limits, idempotency, safe-disable,
  receipts, redaction, CLI/API parity, and focused tests.
- If that cannot be proven, stop at preview/readiness contracts and emit an
  exact future unblock prompt.
- Agent output is untrusted proposal text, never authority.
- Safety summary: no arbitrary command strings are allowed.
- UAA durable evidence must not store raw prompts, raw responses, raw provider
  payloads, raw logs, sensitive paths, usernames, hostnames, credentials, or
  secret-like values.
- Control Center is a shell; Python Agent Core owns product truth.

## Prompt Sequence

1. `01_baseline_authority_and_product_truth.prompt.md`
2. `02_pair_run_contracts_and_state_machine.prompt.md`
3. `03_adapter_registry_policy_and_approval_gate.prompt.md`
4. `04_foreground_relay_runner_orchestrator.prompt.md`
5. `05_transcript_artifacts_receipts_and_evidence.prompt.md`
6. `06_coding_chat_cli_api_ui_surfaces.prompt.md`
7. `07_final_hardening_and_graduation_truth.prompt.md`

## Required End State

```text
operator starts pair run
-> UAA validates task, scope, agents, turn budget, stop conditions
-> UAA blocks with exact reason or starts approved foreground adapters
-> each agent receives bounded turn packets
-> UAA captures each turn as redacted artifacts and receipts
-> stop on max turns, timeout, sentinel completion, user stop, error, or approval need
-> final summary includes disagreements, candidate changes, validation plan, and blocked authority
```

## Final Verification

Run focused tests for changed files plus the relevant subset of:

```bash
git diff --check
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py
.venv/bin/python scripts/verify_operational_maturity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_coding_cockpit_read_model.py -q
.venv/bin/python -I -B -S scripts/run_foundation_gate.py --command-mode report-only
make frontend-check
```

Report phase status, whether foreground paired-agent execution was safely
promoted or blocked, exact authority granted if any, files changed,
CLI/API/UI surfaces, tests run, evidence/redaction behavior, remaining risks,
and next exact lane.
