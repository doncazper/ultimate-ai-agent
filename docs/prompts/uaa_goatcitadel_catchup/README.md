# UAA GoatCitadel Catch-Up Prompt Pack

Status: stored execution prompts, not runtime authority

Purpose: accelerate UAA toward GoatCitadel-level agent-platform maturity while
preserving UAA's contract-first Python Agent Core, local-first authority model,
redacted evidence posture, CLI/API parity, and Founder Command Center product
spine.

This pack treats GoatCitadel as a reference system to inspect for product and
architecture patterns, not as a dependency to import or code to copy. The
operator running the pack must prove each UAA capability with UAA code, tests,
route contracts, CLI/API surfaces, Control Center UX, redacted evidence, and
product-language truth.

## Wrapper Command

From the repo root:

```bash
bash scripts/dev/run_uaa_goatcitadel_catchup_prompt_pack.sh
```

Dry-run and emit the combined prompt without invoking Codex:

```bash
bash scripts/dev/run_uaa_goatcitadel_catchup_prompt_pack.sh --dry-run
```

Emit a reviewable combined prompt to a chosen path:

```bash
bash scripts/dev/run_uaa_goatcitadel_catchup_prompt_pack.sh --dry-run --output /tmp/uaa-goatcitadel-catchup.md
```

## Prompt Order

1. `00_execute_uaa_goatcitadel_catchup_end_to_end.prompt.md`
2. `01_reference_gap_truth_and_age_adjusted_scoreboard.prompt.md`
3. `02_productized_agent_loop_spine.prompt.md`
4. `03_durable_orchestration_progress_and_recovery.prompt.md`
5. `04_action_tool_code_lanes_and_approval_receipts.prompt.md`
6. `05_memory_learning_context_and_feedback.prompt.md`
7. `06_evidence_audit_receipts_and_observability.prompt.md`
8. `07_model_provider_research_and_external_info_posture.prompt.md`
9. `08_cockpit_cli_api_parity_and_operator_ux.prompt.md`
10. `09_extensibility_ecosystem_and_final_hardening.prompt.md`

Use `00_execute_uaa_goatcitadel_catchup_end_to_end.prompt.md` when the
operator wants a single orchestrated run. The wrapper sends that prompt to
Codex after validating the bundle hash and file list.

## Catch-Up Target

The pack aims to make UAA stronger in the areas where GoatCitadel has a more
operator-visible product shape:

- Mission Control-style cockpit clarity;
- durable run lifecycle, checkpoints, progress, resume, and recovery;
- action/tool/code execution lanes with approval, receipts, hashes, and
  reviewability;
- memory lifecycle with review, feedback, quality, provenance, and correction;
- evidence receipts and audit surfaces that operators can inspect;
- model/provider/catalog posture with cost and readiness literacy;
- inspectable extension/capability catalogs with activation boundaries;
- benchmark and release-proof habits.

The pack also protects UAA's current strengths:

- Python Agent Core remains the brain;
- Control Center remains a shell, not authority;
- policy, approval, route classification, OpenAPI, and Foundation Gate checks
  stay hard boundaries;
- no broad autonomy or production authority is inferred from UI, docs, or
  prompt execution;
- every mutation lane remains exact-scoped, approval-bound, idempotent,
  auditable, rollback-aware, redacted, and tested.

## Authority Boundary

This bundle does not grant runtime model calls, provider SDK calls, live web
fetching, browser automation, connector writes, unrestricted shell/subprocess
execution, plugin runtime import, memory writes, context injection, remote
execution, public beta/release claims, production authority, or broad autonomy.

If a phase discovers that a GoatCitadel-style capability requires one of those
authorities, it must produce a no-go posture or an exact future authority
graduation prompt. It must not silently implement the authority.

## Verification

Validate the bundle:

```bash
.venv/bin/python scripts/verify_uaa_goatcitadel_catchup_prompt_pack.py
```

Run the focused unit test:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_goatcitadel_catchup_prompt_pack.py -q
```

