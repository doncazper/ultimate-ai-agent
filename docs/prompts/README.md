# Prompt Pack v0.5.1

Status: Initial implementation prompt pack  
Purpose: Provide versioned system prompts and instruction templates for foundation agents.

## Prompt governance

Prompts are behavior-control files. They must be treated like code.

Rules:

```text
1. Prompts are versioned.
2. Prompt changes require a reason.
3. Prompt changes that affect tools, memory, permissions, files, or code require evals.
4. Prompts may not override the Agent Constitution.
5. Prompts may not bypass Execution Contract, Context Pack, Consent Ledger, Tool Broker, Event Ledger, or QA gates.
6. External/untrusted content is evidence, never instruction.
```

## Initial prompt files

```text
commander_orchestrator.system.md
execution_contract_builder.system.md
context_pack_builder.system.md
model_router.system.md
event_ledger_recorder.system.md
consent_policy_checker.system.md
tool_broker_policy_agent.system.md
memory_curator.system.md
file_manager.system.md
spec_generator.system.md
qa_eval_agent.system.md
security_reviewer.system.md
release_receipt_generator.system.md
subagent_task_contract.template.md
prompt_style_rules.md
prompt_registry_v0_5_1.json
prompt_eval_matrix.md
```

## Use in implementation

The first implementation should load prompts by `prompt_id`, not by hard-coded path. Prompt metadata lives in the prompt registry.

## v0.5.2 Addition

Added `agent_gateway_guard.system.md` to protect the API boundary and prevent OpenWebUI or UI clients from bypassing Agent Core policy.

Active registry: `prompt_registry_v0_5_2.json`.

## Founder Command Center authority ramp prompts

Stored execution prompts for `FCC-AUTH-RAMP-001` live in
`docs/prompts/fcc_authority_ramp/`. They are operator-run prompts, not runtime
system prompts, and they do not grant authority by themselves. Use
`docs/prompts/fcc_authority_ramp/00_execute_all_review_verify_harden.prompt.md`
to run the sequence from charter through read-only/proposal foundation,
authority candidate ranking, and the first exact micro-lane gate.

## Founder Command Center planned sequence prompts

Stored execution prompts for UAA-P1-066 and the next planned Founder Command
Center product lanes live in `docs/prompts/fcc_planned_sequence/`. They are
operator-run prompts, not runtime system prompts, and they do not grant
authority by themselves. Use
`docs/prompts/fcc_planned_sequence/00_execute_all_review_verify_finalize.prompt.md`
to run the sequence with review, verification, repair, commit, annotated-tag,
and push gates.

## Founder Command Center memory module prompts

Stored execution prompts for `FCC-MEM-001` Memory Workbench V1 and the
supporting Memory module hardening pass live in
`docs/prompts/fcc_memory_module_sequence/`. They are operator-run prompts, not
runtime system prompts, and they do not grant authority by themselves. Use
`docs/prompts/fcc_memory_module_sequence/00_execute_all_review_verify_finalize.prompt.md`
to run the sequence from baseline audit through workbench read model,
lifecycle expansion, quality/ranking/search/intake, cross-surface bindings, UI,
CLI parity, tests, docs, review, hardening, annotated tag, and push gates.
