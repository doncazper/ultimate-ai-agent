# Execute UAA-RUNTIME-PARITY-001 End To End

Role: Principal AI agent runtime architect, product strategist, security
reviewer, implementation lead, and adversarial hardening reviewer for UAA.

Goal: make UAA's real operation loop materially competitive with external comparison runtime's
runtime/orchestration loop by implementing UAA-native route binding, durable
turn/run/approval state, staged orchestration, chat-turn preparation, provider
selection evidence, exact action receipts, and cockpit/CLI/API parity.

This is not a broad repo audit. Focus on the runtime loop and the scorecard:
turn-contract clarity, authority/safety boundary, execution readiness, durable
runtime integration, model/provider routing, operator inspectability, product
usefulness today, and long-term safe foundation.

## Read First

Read these files completely before implementation:

- `AGENTS.md`
- `README.md`
- `VERSION.md`
- `SECURITY.md`
- `docs/prompts/uaa_runtime_parity/README.md`
- every prompt in `docs/prompts/uaa_runtime_parity/`
- current product and authority references:
  - `docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md`
  - `docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md`
  - `docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md`
  - `docs/architecture/TURN_CONTRACT_ROUTER.md`
  - `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
  - `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
  - `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
  - `docs/api/openapi_contract.md`
  - `docs/api/route_inventory.md`

Inspect current UAA implementation before editing:

```bash
pwd
git status --short --branch
git branch --show-current
git rev-parse HEAD
rg "TurnDecision|InvocationPolicy|route decision|durable run|approval|orchestration|runtime|model router|provider|receipt|evidence|idempotency|retry|resume|cancel" src tests apps docs scripts
```

If the sibling external comparison runtime repo is available, inspect it read-only for reference
patterns only:

- `external-runtime-ref:gateway-chat-messages`
- `external-runtime-ref:model-selector`
- `external-runtime-ref:orchestration-engine`
- `external-runtime-ref:chat-turn-prep-service`
- `external-runtime-ref:canonical-runtime-state-model`

## Global Rules

- Treat `AGENTS.md` as binding.
- Preserve unrelated dirty files and user changes.
- Do not copy external runtime code wholesale, import external runtime packages, or adopt
  external comparison runtime authority assumptions.
- Reimplement borrowed patterns in UAA-native Python core contracts, route
  contracts, CLI, Control Center, docs, tests, and verifiers.
- Do not add runtime model calls, provider SDK calls, live web fetching,
  browser automation, connector writes, unrestricted shell/subprocess
  execution, plugin runtime import, remote execution, public release claims,
  production authority, or broad autonomy.
- Python Agent Core remains the brain.
- Control Center and OpenWebUI remain shells, not authority.
- Product behavior must not live only in React state.
- Every operator-relevant mutation or durable state must have core/API/CLI
  parity and tests.
- Store safe refs, redacted summaries, bounded previews, hashes, and receipts;
  do not persist raw prompt, response, provider payload, local path, raw log,
  username, hostname, credential, or secret-like values.
- Every route change must update OpenAPI/API manifest checks and side-effect
  classification.
- If a capability remains blocked, expose the blocker clearly and create an
  exact follow-up lane prompt instead of claiming parity.

## Prompt Sequence

Execute these prompts in order:

1. `01_baseline_scoreboard_and_gap_truth.prompt.md`
2. `02_live_route_decision_binding.prompt.md`
3. `03_turn_run_approval_state_model.prompt.md`
4. `04_staged_orchestration_engine.prompt.md`
5. `05_chat_turn_preparation_loop.prompt.md`
6. `06_role_based_model_provider_evidence.prompt.md`
7. `07_mature_action_execution_and_signed_evidence.prompt.md`
8. `08_cockpit_cli_api_parity_and_final_hardening.prompt.md`

## Execution Loop

For each phase:

1. Inspect existing UAA code and tests before editing.
2. Classify relevant capability state as `implemented`, `partial`, `planned`,
   `mock-only`, `blocked`, `deprecated`, `contradicted`, or `unknown`.
3. Implement the smallest UAA-native slice that moves the runtime parity loop.
4. Add focused tests, verifiers, docs, and product-truth updates.
5. Run focused checks for changed files.
6. Review the diff adversarially for:
   - authority creep;
   - UI-only truth;
   - raw prompt/response/log/path/provider payload persistence;
   - route/API manifest drift;
   - missing CLI parity;
   - stale route-decision reuse;
   - missing approval scope validation;
   - missing idempotency, replay, retry, resume, rollback, or safe-disable
     posture;
   - product-language overclaims;
   - unsupported parity claims against external comparison runtime.
7. Fix and harden before moving to the next phase.

If the full sequence becomes too large for one reviewable change set, finish
the strongest coherent slice, document the remaining blocked/deferred work, and
emit exact follow-up prompts. Do not leave a half-wired runtime loop or claim
parity without evidence.

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
.venv/bin/python -I -B -S scripts/run_foundation_gate.py --command-mode report-only
make frontend-check
make frontend-visual-check
```

Run frontend checks only when frontend files changed. If an environment
dependency blocks a check, report it and do not claim success.

## Final Response Requirements

Report:

- prompt sequence executed;
- phase status: implemented, partial, blocked, or deferred;
- before/after scorecard for the eight parity dimensions;
- files changed;
- external comparison runtime patterns adapted as UAA-native designs;
- external comparison runtime patterns explicitly not merged or not appropriate;
- authority still blocked;
- tests/verifiers run with pass/fail/blocker;
- hardening loops completed and faults fixed;
- remaining risks;
- current git status summary;
- recommended next exact prompt or PR lane.
