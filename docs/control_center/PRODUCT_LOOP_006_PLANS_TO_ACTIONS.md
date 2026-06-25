# Product Loop 006 Plans To Reviewable Action Envelopes Upgrade

Status: implemented as a backend-owned local read model.

Product Loop 006 adds `plans_to_actions_bridge_read_model` to the existing
Today and Action Inbox read routes:

```text
contract-ref:product-loop-006-plans-to-reviewable-action-envelopes:v1
```

The read model maps plan proposals and task-decomposition proposal refs to
reviewable Action envelope posture. It exposes safe refs for:

- risks and reasons
- task-decomposition proposal and review-envelope refs
- expected receipt refs
- rollback refs
- safe-disable refs
- blocked authority refs
- linked Action Inbox proposal refs

This is proposal-only review metadata. Approval refs are identifiers and
decision receipts only; they do not execute, authorize tools or workflows, call
models or providers, run shell or browser work, use connectors, write memory,
inject context, or grant production authority.

The companion CLI inspection path is:

```bash
PYTHONPATH=src .venv/bin/python scripts/inspect_plans_to_actions_bridge.py
```

Inspection is read-only, safe-ref-only, and redacted. Evidence and bridge
records must not include raw prompt content, raw response content, raw provider
payload content, raw local path content, raw log content, account identifiers,
usernames, hostnames, credentials, secrets, or environment dumps. Missing
backend bridge data fails closed in Control Center; React does not backfill
plan-to-action envelopes from mock data.

## Verification Lane

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_plans_to_actions_bridge.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_p1_073_plans_action_envelopes.py tests/test_uaa_p1_090_task_decomposition_proposal_engine.py
PYTHONPATH=src .venv/bin/python scripts/verify_product_loop_006_plans_to_actions.py
```

## Still Blocked

This lane adds no provider/model calls, no tool execution, no workflow
execution, no action execution, no shell/subprocess execution, no browser
execution, no connector runtime, no connector writes, no memory writes, no
context injection, autonomous planning authority, public beta, distribution, or
production authority.
