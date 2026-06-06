# M67 Revocation + Kill Switch Contracts

The M67 contract surface defines a review-only `RevocationKillSwitchRecord`.
The record is exact-bound to a validated M66 scoped approval bundle and exists
only to document revocation requested and kill-switch requested intent.

## Required Bindings

Each record must bind:

- `revocation_record_ref`
- `bundle_ref`
- `source_scope_ref`
- `audit_view_ref`
- `simulation_result_ref`
- `actor_ref`
- `resource_refs`
- `capability_refs`
- `allowlist_refs`
- `approval_refs`
- `revocation_ref`
- `audit_ref`
- `replay_ref`

The validator revalidates the scoped approval bundle at evaluator boundaries.
If the current bundle has hidden drift, unsafe metadata, authority flags, test
approval refs, revoked/expired/replay-used state, or side effects, the M67
record is denied.

## Required State

- `record_valid_for_review=True`
- `review_only=True`
- `deterministic=True`
- `revocation_requested=True`
- `kill_switch_requested=True`
- `approval_refs_are_identifiers_only=True`
- `actor_bound=True`
- `resource_bound=True`
- `capability_bound=True`
- `allowlist_bound=True`
- `non_transferable=True`
- `replay_safe=True`

## Denied State

The contract denies hidden authority or runtime behavior:

- `revocation_performed=True`
- `kill_switch_activated=True`
- `session_stopped=True`
- `policy_activation_requested=True`
- `session_start_requested=True`
- `session_active=True`
- `autonomous_actions_enabled=True`
- `background_worker_enabled=True`
- `execution_requested=True`
- `execution_performed=True`
- `tool_execution_enabled=True`
- `shell_execution_enabled=True`
- `network_tool_enabled=True`
- `browser_automation_enabled=True`
- `plugin_execution_enabled=True`
- `mobile_sensor_enabled=True`
- `remote_execution_enabled=True`
- `memory_write_enabled=True`
- `context_injection_enabled=True`
- `model_provider_call_enabled=True`
- `production_authority_enabled=True`
- `authority_granted=True`

M67 adds no backend route, no dependency, and no M68 work.
