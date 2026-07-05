# CRM Local Command Center Prompt Bundle

Status: Stored execution prompts for UAA's local-first CRM command center.

Purpose: Build UAA CRM from the current fixture-only shell into a governed,
local-first relationship operating system. The bundle mines public feature
patterns from paid CRM products such as Follow Up Boss and Wise Agent without
copying proprietary code, UI, copy, data, screenshots, templates, or branding.

These prompts are operator-run instructions. They do not grant runtime
authority by themselves and do not replace `AGENTS.md`,
`docs/control_center/OPERATOR_SHELL_GAP_MAP.md`,
`docs/control_center/PRODUCT_LANGUAGE_RULES.md`, route manifests, release
surface manifests, or OpenAPI.

## Product Target

UAA CRM should become a free, local-first relationship command center for the
operator:

- Relationship database.
- People and organization records.
- Relationship timeline.
- Follow-up queue.
- Smart lists.
- Pipeline and opportunity board.
- Communication draft center.
- Action plans and playbooks.
- Memory and evidence-backed contact summaries.
- AI proposal layer where existing exact-governed authority permits it.
- Proof and receipt trail.
- Import/export.
- Optional exact-approved connector and sending lanes later.

The governing loop is:

```text
Relationship signal -> Evidence/Memory context -> Suggested follow-up -> Action
Inbox approval -> Receipt/Proof -> Relationship timeline update
```

## Prompt Order

1. `01_crm_product_truth_feature_map.prompt.md`
2. `02_crm_backend_read_model.prompt.md`
3. `03_crm_control_center_cockpit.prompt.md`
4. `04_crm_local_storage_seed.prompt.md`
5. `05_crm_relationship_timeline.prompt.md`
6. `06_crm_follow_up_queue.prompt.md`
7. `07_crm_smart_lists.prompt.md`
8. `08_crm_pipeline_board.prompt.md`
9. `09_crm_exact_local_mutations.prompt.md`
10. `10_crm_communication_drafts.prompt.md`
11. `11_crm_ai_proposal_layer.prompt.md`
12. `12_crm_local_import_export.prompt.md`
13. `13_crm_reporting.prompt.md`
14. `14_crm_connector_read_lanes.prompt.md`
15. `15_crm_sends_writes_authority_plan.prompt.md`
16. `16_crm_qa_gate.prompt.md`

Use `00_execute_crm_local_command_center_end_to_end.prompt.md` for an
end-to-end run.

## Authority Boundary

The pack should graduate useful local CRM capability first. External writes,
sends, account sync, connector writes, provider/model calls, browser automation,
background autonomy, public beta claims, public release claims, and production
authority remain blocked unless a specific phase implements an exact lane with
approval binding, idempotency, receipts, redaction, safe-disable, rollback or
compensation posture, CLI/API parity, and focused verifier coverage.
