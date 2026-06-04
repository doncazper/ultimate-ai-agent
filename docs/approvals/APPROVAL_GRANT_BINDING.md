# Approval Grant Binding

Status: active
Current through: v0.32.1
Purpose: Record actor/action/resource/scope binding rules for M28.

An M28 approval grant is valid for policy only when it binds the same actor,
action, resource, and scope as the action intent being evaluated.

Required binding:

- `actor_ref` must match the intent actor.
- `action_ref` must match the intent action.
- `resource_ref` must match the intent resource.
- scope actor/action/resource refs must match the grant and intent.
- wildcard scope is denied.

Binding success does not authorize execution. It only allows a safe policy
decision when all other action-policy checks pass and the action is no-effect or
read-metadata. M28 keeps action execution, tool execution, memory writes, file
mutation, network calls, model/provider calls, shell execution, browser/mobile/
remote/plugin actions, backend execution routes, and production authority
blocked.

M29-M40 remain planned/provisional.
