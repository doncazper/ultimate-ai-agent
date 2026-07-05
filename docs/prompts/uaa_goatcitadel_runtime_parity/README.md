# UAA GoatCitadel Runtime Parity Prompt Pack

Status: stored execution prompts, not runtime authority

Purpose: push UAA toward GoatCitadel-level real operation-loop maturity while
preserving UAA's contract-first Python Agent Core, local-first authority model,
redacted evidence posture, and Control Center shell boundary.

This pack treats GoatCitadel as a read-only architectural reference. It may
adapt patterns, failure modes, and product contracts, but it must not import
GoatCitadel packages or copy implementation code wholesale. Every improvement
must be reimplemented in UAA-native Python core, API, CLI, Control Center, docs,
tests, and verifiers.

## Wrapper Command

From the repo root:

```bash
bash scripts/dev/run_uaa_goatcitadel_runtime_parity_prompt_pack.sh
```

Dry-run and emit the combined prompt without invoking Codex:

```bash
bash scripts/dev/run_uaa_goatcitadel_runtime_parity_prompt_pack.sh --dry-run
```

Emit a reviewable combined prompt to a chosen path:

```bash
bash scripts/dev/run_uaa_goatcitadel_runtime_parity_prompt_pack.sh --dry-run --output /tmp/uaa-goatcitadel-runtime-parity.md
```

## Prompt Order

1. `00_execute_runtime_parity_end_to_end.prompt.md`
2. `01_baseline_scoreboard_and_gap_truth.prompt.md`
3. `02_live_route_decision_binding.prompt.md`
4. `03_turn_run_approval_state_model.prompt.md`
5. `04_staged_orchestration_engine.prompt.md`
6. `05_chat_turn_preparation_loop.prompt.md`
7. `06_role_based_model_provider_evidence.prompt.md`
8. `07_mature_action_execution_and_signed_evidence.prompt.md`
9. `08_cockpit_cli_api_parity_and_final_hardening.prompt.md`

Use `00_execute_runtime_parity_end_to_end.prompt.md` when the operator wants a
single orchestrated run. The wrapper validates the bundle hash and file list,
then sends the end-to-end prompt to Codex.

## Runtime Parity Target

The target loop is:

```text
operator input
-> turn classification
-> route decision binding
-> durable turn/run creation
-> staged orchestration plan
-> approval wait or exact action proposal
-> approved execution lane when already authorized
-> signed portable evidence receipt
-> operator-visible result, blocked state, or retry/recovery path
```

The attached scorecard target is to preserve UAA's strengths while closing the
GoatCitadel gaps:

| Dimension | Current UAA Target | Parity Target |
|---|---:|---:|
| Turn-contract clarity | 9 | 9+ |
| Authority/safety boundary | 9 | 9+ |
| Execution readiness | 5 | 8+ |
| Durable runtime integration | 5 | 8+ |
| Model/provider routing | 3 | 7+ evidence-first |
| Operator inspectability | 8 | 8+ |
| Product usefulness today | 6 | 8+ |
| Long-term safe foundation | 9 | 9+ |

## GoatCitadel Reference Patterns

Inspect these read-only when the sibling repo is available:

- `../GoatCitadel/apps/gateway/src/routes/chat.messages.ts`
- `../GoatCitadel/apps/gateway/src/orchestration/model-selector.ts`
- `../GoatCitadel/apps/gateway/src/orchestration/engine.ts`
- `../GoatCitadel/apps/gateway/src/services/chat-turn-prep-service.ts`
- `../GoatCitadel/docs/CANONICAL_RUNTIME_STATE_MODEL.md`

Borrow the architecture, not the implementation.

## Authority Boundary

This bundle does not grant runtime model calls, remote provider SDK calls, live
web fetching, browser automation, connector writes, unrestricted shell or
subprocess execution, plugin runtime import, context injection, remote
execution, public release claims, production authority, or broad autonomy.

If parity requires an authority that UAA has not accepted yet, implement the
blocked/readiness/proposal surface and create an exact future graduation prompt
instead of silently granting the authority.

## Verification

Validate the bundle:

```bash
.venv/bin/python scripts/verify_uaa_goatcitadel_runtime_parity_prompt_pack.py
```

Run the focused unit test:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_goatcitadel_runtime_parity_prompt_pack.py -q
```

