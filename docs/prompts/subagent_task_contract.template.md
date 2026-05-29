# Subagent Task Contract Template v0.5.1

Use this template whenever the Orchestrator delegates to a specialist agent.

```yaml
subagent_task_id: ""
run_id: ""
contract_id: ""
parent_context_pack_id: ""
subagent_role: "research | builder | qa | memory_curator | file_manager | security | spec_generator | other"
goal: ""
inputs_allowed:
  - ""
inputs_forbidden:
  - ""
canonical_sources:
  - ""
memory_sources:
  - ""
tools_allowed:
  - ""
tools_forbidden:
  - ""
model_class_allowed: ""
risk_level: "low | medium | high | critical"
privacy_level: "public | project_private | personal_sensitive | restricted"
acceptance_criteria:
  - ""
output_format: ""
logging_required: true
approval_required: false
rollback_required: false
```

Subagents may not expand their own scope. They must return blocked/needs_orchestrator_decision if the task requires new tools, new context, new permissions, or higher autonomy.
```
