# Prompt Eval Matrix v0.5.1

Purpose: Define minimum evals before prompt changes are accepted.

| Prompt | Required evals before production use |
|---|---|
| Commander / Orchestrator | execution_contract_eval, context_pack_eval, approval_gate_eval, foundation_gate_eval |
| Execution Contract Builder | execution_contract_eval, foundation_gate_eval |
| Context Pack Builder | context_pack_eval, canonical_precedence_eval, consent_permission_eval |
| Model Router | model_routing_eval, model_cost_efficiency_eval, model_privacy_routing_eval |
| Event Ledger Recorder | event_ledger_eval, observability_replay_eval |
| Consent Policy Checker | consent_permission_eval, approval_gate_eval |
| Tool Broker Policy Agent | tool_broker_eval, approval_gate_eval |
| Memory Curator | memory_service_eval, canonical_precedence_eval |
| File Manager | file_manager_eval, canonical_precedence_eval |
| QA / Eval Agent | foundation_gate_eval, contract_test_matrix |
| Security Reviewer | prompt_injection_cross_source_eval when added, excessive_agency_eval when added |

Prompt changes that weaken approval, logging, consent, canonical precedence, privacy, or eval requirements require explicit review.
