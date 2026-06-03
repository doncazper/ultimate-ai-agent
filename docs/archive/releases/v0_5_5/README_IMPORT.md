Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# README Import Guide v0.5.5

Status: Active pre-coding baseline.

## Purpose

v0.5.5 adds the final local-agent infrastructure contracts needed before coding:

```text
Structured World State
Context Budget Manager
Token accounting and calibration
Strategic tool-result retention/trimming
Prompt/tool prefix cache policy
Local runtime and offline infrastructure
Local runtime optimization profiles
Agent SDK and A2A adapter strategy
Long-running session survival evals
```

## Import checklist

1. Confirm the repo is clean.
2. Apply the v0.5.5 snapshot or patch.
3. Historical verifier path after v0.29.4 archive repair:
   `python3 docs/archive/releases/v0_5_5/legacy_verifier_v0_5_5.py`.
4. Commit with `docs: add local runtime and context survival foundation v0.5.5`.
5. Tag `v0.5.5`.

## Read order

```text
README.md
VERSION.md
ultimate_ai_agent_master_plan_v0_5_5.md
docs/canonical/09_roadmap.md
docs/canonical/53_structured_world_state.md
docs/canonical/54_context_budget_and_session_survival.md
docs/canonical/57_local_runtime_and_offline_agent_infrastructure.md
docs/canonical/58_agent_sdk_and_a2a_adapter_strategy.md
docs/implementation/foundation_gate_implementation_plan_v0_5_5.md
```

## Foundation boundary

v0.5.5 does not authorize implementation of advanced modules. It only adds architecture, schemas, and eval specifications.
