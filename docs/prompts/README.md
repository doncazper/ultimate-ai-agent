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

## Fusion routing and delegation prompts

Stored execution prompts for work classification, route/delegation visibility,
future-only sidekick proposal envelopes, cache/context economics refs, private
dogfood evidence, and product-language guards live in
`docs/prompts/fcc_fusion_routing_delegation_prompts.md`. They are operator-run
prompts, not runtime system prompts, and they do not grant runtime model calls,
sidekick execution, action execution, provider/model authority, connector
writes, memory writes, context injection, public beta, production authority, or
broader autonomy. Use Prompt 00 in that file to run the nine-task sequence end
to end.

## CRM product sequence prompts

Stored execution prompts for the CRM product-line sequence live in
`docs/prompts/crm_product_sequence.md`. They start from the contract-only
CRM + Communications Spine M0 foundation and gate CRM M1 fixture-only vertical
screens, M2 read-model planning, communications metadata, work queues,
relationship graph posture, proposal lanes, and later exact local-write
candidates without granting connector runtime, external CRM writes, sends,
calendar writes, account sync, provider/model calls, public beta, or
production authority. Use Prompt 00 in that file for an end-to-end gated run.

## Next capability and product prompts

Stored execution prompts for the next capability/product catch-up sequence live
in `docs/prompts/uaa_next_capability_product_prompts.md`. They cover MCP
gateway foundation, A2A gateway foundation, browser automation through
WebAccessGateway, release-surface proof, macOS setup polish, visual
regression, durable operator-state recovery, provider/settings diagnostics,
product-forward front-door copy, and the unified Chat -> Plan -> Action ->
Evidence thread. They are operator-run prompts, not runtime system prompts,
and they do not grant MCP/A2A/browser/runtime authority by themselves. Use
Prompt 00 in that file to split the pack into small, merge-gated PR lanes;
do not run the whole pack as one implementation by default.

## Public-facing portfolio/developer-preview readiness pass

The UAA-specific public-facing readiness prompt lives in
`docs/prompts/uaa_public_preview_perfection_pass.prompt.md`. It adapts a
generic repo-polish/public-preview prompt to UAA's current truth: Founder
Command Center positioning, local-first governed Agent Core, public
portfolio/developer-preview readiness, product-language honesty, sanitized
visuals, release-surface proof, and no public beta/release/distribution or
broad runtime authority claims.
