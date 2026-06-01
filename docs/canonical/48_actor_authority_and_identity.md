# 48 — Actor, Authority, and Identity

Status: Active foundation contract, v0/provisional until Foundation Gate.

## Purpose

The agent must distinguish between actions requested by the user, actions initiated by the Orchestrator, scheduled jobs, scanners, provider callbacks, tool workers, and future self-improvement processes.

## Core rule

> Every meaningful operation must identify the actor, the user/project it acts on behalf of, and the authority source that permits it.

## Actor types

```text
human_user
orchestrator
subagent
scheduled_job
scanner
tool_broker
provider_adapter
system_worker
self_improvement_worker
admin
external_callback
```

## Authority sources

```text
explicit_user_request
approved_execution_contract
active_consent_grant
standing_approval
admin_policy
system_policy
foundation_test
manual_operator_action
```

## ActorContext fields

```text
actor_type
actor_id
actor_display_name
on_behalf_of_user_id
workspace_id
project_id
authority_source
execution_contract_id
consent_ref
approval_ref
session_id
created_at
```

## Rules

1. `human_user` authority from explicit current instruction outranks old memory or defaults.
2. `scanner` and `scheduled_job` may not initiate external mutable actions directly.
3. `self_improvement_worker` may not modify Trusted Computing Base files.
4. `subagent` actions inherit authority from the Orchestrator's Execution Contract and cannot expand their own authority.
5. Tool Broker must reject operations missing ActorContext.

## Why this matters

When a future alert fires, the user should know whether it came from a watchlist, a scanner, a scheduled digest, a manually requested research task, or an agent inference. This distinction is a trust requirement.

## Future Mobile Actor Authority

A mobile app, paired device, push notification, OS permission, or arbitrary approval string is not authority by itself. Mobile actions must carry ActorContext, consent refs, approval refs, and event refs through the Agent API Boundary.

Phone/mobile cannot approve its own hidden sensor capture, cannot elevate autonomy, and cannot convert sensor output into trusted control input.
