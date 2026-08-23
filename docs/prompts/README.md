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

## Founder Command Center Authority Graduation Program prompts

Stored execution prompts for the `FCC-AUTH-RAMP-001` Authority Graduation
Program live in `docs/prompts/fcc_authority_ramp/`. They are operator-run
prompts, not runtime system prompts, and they do not grant authority by
themselves. Use
`docs/prompts/fcc_authority_ramp/00_execute_all_review_verify_harden.prompt.md`
to run the sequence from charter through the fixed first implementation lane:
`read_only_real_world_web_fetch` through `WebAccessGateway`, follow-on
authority candidate ranking, and the follow-on micro-lane graduation gate.

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

## CRM Local Command Center prompts

Stored execution prompts for the CRM Local Command Center live in
`docs/prompts/crm_local_command_center/`. They sequence UAA-native CRM work from
product truth and backend-owned read models through local storage, timelines,
follow-up queues, smart lists, pipeline views, drafts, import/export, reporting,
connector-read planning, and later sends/writes authority planning. They are
operator-run prompts, not runtime system prompts, and they do not grant CRM
connector writes, sends, account sync, provider/model calls, browser automation,
background autonomy, public release claims, or production authority by
themselves. Use
`docs/prompts/crm_local_command_center/00_execute_crm_local_command_center_end_to_end.prompt.md`
for the end-to-end wrapper.

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

## Skill Workbench discovery and adoption prompts

Stored execution prompts for the Skill Workbench discovery and adoption
sequence live in `docs/prompts/skill_workbench_adoption_prompt_pack.md`. They
cover external skill marketplace metadata discovery, read-only Skills tab
UX, adoption candidates, quarantine contracts, static review, UAA-owned
rewrite/adaptation, local registry gates, and product-language verifiers.
They are operator-run prompts, not runtime system prompts, and they do not
grant marketplace install, external code execution, plugin runtime import,
browser automation, connector writes, credential access, or production
authority. Use Prompt 00 in that file to run the sequence as small
merge-gated PR lanes.

## Turn Contract Router productization prompts

Stored execution prompts for productizing the merged Turn Contract Router live
in `docs/prompts/turn_contract_router_productization_prompt_pack.md`. They add
parallel preflight contracts, central arbitration, CLI/API preview, Control
Center diagnostics, chat/harness binding, browser product smoke checks, and a
review/fix/harden sweep without granting broad runtime, browser, connector,
provider/model, or production authority by themselves. Use
`docs/prompts/turn_contract_router_productization_execute_end_to_end.prompt.md`
for the strict enterprise integration wrapper that executes each phase
one-at-a-time with review, fix, hardening, tests, browser smoke, PR merge, and
final gap reporting gates.

## Kanban Board / Work Board prompts

Stored execution prompts for the UAA Work Board / Kanban cockpit live in
`docs/prompts/kanban_board/`. They cover the backend-owned read model, API/CLI
inspection, local-only drag/drop and keyboard preview, list/proof views,
blocked persistence posture, tests, docs, and release-surface alignment. They
are operator-run prompts, not runtime system prompts, and they do not grant
durable board mutation, issue tracker writes, connector writes, provider/model
calls, shell/subprocess execution, browser automation, background autonomy,
public beta/release, or production authority. Use
`docs/prompts/kanban_board/00_execute_kanban_board_end_to_end.prompt.md` for the
end-to-end wrapper.

## Hermes Runtime Adoption prompts

Stored execution prompts for adopting Hermes Agent patterns into UAA-native
governed runtime delegation live in `docs/prompts/hermes_runtime_adoption/`.
They cover 45 merge-gated phases, including runtime delegation, capability
discovery, run/event/approval posture, provider/catalog UX, toolsets, memory,
skills, context refs, rollback, orchestration, coding, diagnostics, MCP/plugin
metadata, parity evals, and final reporting. They are operator-run prompts, not
runtime system prompts, and they do not copy Hermes code or grant broad runtime
authority by themselves. Use
`docs/prompts/hermes_runtime_adoption/00_execute_all_45_review_fix_merge_harden.prompt.md`
for the strict wrapper.

## Hermes/OpenClaw parity gap closure prompts

Stored execution prompts for closing the July 2026 Hermes Agent and OpenClaw
parity recommendations live in `docs/prompts/uaa_parity_gap_closure/`. The
wrapper takes a fresh inventory of current `main`, open and recently merged
pull requests, branches, worktrees, manifests, tests, and—when task tools are
available—other active UAA Codex tasks before every phase. Only merged,
meaningfully tested, backend-owned behavior is skipped; open PRs, mocks,
contracts, plans, static renders, and disabled adapters do not count as
implemented runtime behavior. Each unresolved phase is implemented, hardened,
verified, committed, pushed, reviewed, and merged before the inventory is
refreshed for the next phase. The pack itself grants no runtime authority. Use
`docs/prompts/uaa_parity_gap_closure/00_execute_parity_gap_closure_end_to_end.prompt.md`
or `scripts/dev/run_uaa_parity_gap_closure_prompt_pack.sh` for the continuous
wrapper.

## UAA runtime capability foundation prompts

Stored execution prompts for the UAA runtime capability foundation sequence live in
`docs/prompts/uaa_runtime_capability_foundation/`. They sequence UAA-native work from
age-adjusted gap truth through productized loop spine, durable orchestration,
action/tool/code lanes, memory lifecycle, evidence receipts, provider posture,
cockpit parity, extensibility, and final hardening. They are operator-run
prompts, not runtime system prompts, and they do not grant runtime model calls,
provider SDK calls, live web fetching, browser automation, connector writes,
unrestricted shell/subprocess execution, plugin runtime import, memory writes,
context injection, remote execution, public release claims, production
authority, or broad autonomy. Use
`docs/prompts/uaa_runtime_capability_foundation/00_execute_uaa_runtime_capability_foundation_end_to_end.prompt.md`
or `scripts/dev/run_uaa_runtime_capability_foundation_prompt_pack.sh` for the
end-to-end wrapper.

This pack is also the first bundle compiled through UAA's implemented
prompt-module dependency graph. Its `prompt_module_manifest.json` defines the
dependency-first module order and its `prompt_module_golden_receipt.json`
detects source, graph, ordering, or compiled-artifact drift without storing raw
prompt text in the receipt. Use `scripts/dev/uaa_prompt_compiler.py` for generic
graph inspection and compilation. See
`docs/runtime/UAA_PROMPT_MODULE_COMPILER.md` for the exact implemented and
blocked boundaries.

## Messenger Matrix prompts

Stored execution prompts for the macOS-first Messenger Matrix sequence live in
`docs/prompts/messenger_matrix/`. They progress from planning truth and a static
desktop shell through separately accepted exact local harness, session, read,
crypto, manual messaging, room/media, and governed-intelligence lanes. The
bundle itself is planning-only and grants no runtime authority. Prompts 04–10 use
an exact authority-acceptance stage before runtime implementation on the same
branch and PR; every invocation still requires fresh request-scoped evaluation.
Use `scripts/verify_messenger_matrix_prompt_pack.py` to validate bundle order,
integrity, desktop-only scope, and release gates.

## UAA Runtime parity prompts

Stored execution prompts for the focused UAA runtime parity push
live in `docs/prompts/uaa_runtime_parity/`. They target the real
operation loop specifically: live route-decision binding, Turn -> Durable Run
-> Approval linkage, staged orchestration, chat-turn preparation, role-based
model/provider evidence, mature exact action receipts, signed portable
evidence, and cockpit/CLI/API parity. They are operator-run prompts, not
runtime system prompts, and they do not grant runtime model calls, provider SDK
calls, live web fetching, browser automation, connector writes, unrestricted
shell/subprocess execution, plugin runtime import, remote execution, public
release claims, production authority, or broad autonomy. Use
`docs/prompts/uaa_runtime_parity/00_execute_runtime_parity_end_to_end.prompt.md`
or `scripts/dev/run_uaa_runtime_parity_prompt_pack.sh` for the
end-to-end wrapper.

## Coding Pair Agent Relay Runner prompts

Stored execution prompts for the Coding Pair Agent Relay Runner live in
`docs/prompts/coding_pair_agent_relay_runner/`. They target a bounded
foreground paired-agent coding loop where UAA owns the relay state, turn budget,
approval gate, adapter policy, receipts, redaction, and operator-visible
artifacts. They are operator-run prompts, not runtime system prompts, and they
do not grant provider SDK calls, unrestricted shell/subprocess execution,
background autonomy, browser automation, connector writes, Git mutation,
automatic patch apply, public release claims, production authority, or broad
local-agent execution by themselves. Use
`docs/prompts/coding_pair_agent_relay_runner/00_execute_coding_pair_agent_relay_runner_end_to_end.prompt.md`
or `scripts/dev/run_coding_pair_agent_relay_runner_prompt_pack.sh` for the
end-to-end wrapper.

## UAA developer-feedback prompts

Stored prompts for the local, desktop-only UAA Developer Feedback program live
in `docs/prompts/uaa_developer_feedback/`. The pack covers contracts, local
storage, native controls, manual screenshot/video capture, diagnostics, a
Feedback Inbox, post-quit Codex handoff, and a governed patch workflow. The
prompts grant no runtime authority. Capture, media disclosure, Codex launch,
repository mutation, commit, push, and draft-PR creation remain separate exact
capabilities subject to fresh request-scoped evaluation. Use
`docs/prompts/uaa_developer_feedback/00_execute_all_review_verify_harden.prompt.md`
for the finite merge-gated wrapper.

## Governed self-improvement intake summary

`docs/prompts/governed_self_improvement_intake.md` is a bounded, redacted,
superseded intake record for a locally discovered implementation proposal. It
is not executable authority. Its historical blocked posture was superseded by
the materialized recovery contract at
`docs/prompts/remaining_queue_recovery/10_governed_self_improvement.md`, the
exact recovery-manifest binding, and authoritative Queue-of-Record V2 Q29. The
immutable remaining-queue manifest remains audit evidence only. The intake
summary grants no runtime, Git, skill, workflow, learning-write, or merge
authority.
