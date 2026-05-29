# 28 — Rollback and Recovery

Status: Foundation recovery spec, v0.5.3
Owner: Platform / Safety

## Purpose

Every mutating action should have an undo story before it is allowed in production.

## Rollback scope

```text
file writes
memory writes
provider configuration changes
consent changes
watchlist changes
skill installs
code patches
scanner config changes
automation schedules
notification policies
canonical file updates
```

## Required rollback metadata

```text
action_id
run_id
event_id
resource_type
resource_id
before_ref
after_ref
diff_ref
rollback_strategy
rollback_command_or_plan
rollback_risk
approval_ref
created_at
expires_at
```

## Rollback classes

```text
automatic: safe local undo, e.g. replace file with backup
assisted: requires user approval or additional context
manual: documented instructions only
not_supported: allowed only for low-risk read-only or irreversible external facts, not destructive actions
```

## Blocking rule

A mutating high-risk tool call without rollback metadata must be blocked unless a human explicitly accepts the irreversible action.

## Recovery drills

Foundation Gate must include replaying and rolling back the Minimum Lovable Kernel file mutation.
