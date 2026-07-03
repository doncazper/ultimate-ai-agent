# Filesystem Mutation Core Temp-Workspace Evidence

Status: verified core exact lane, Control Center apply route still blocked
Lane: Filesystem Mutation
Promotion level: Level 2 manual foreground action in a temporary workspace
Date: 2026-07-03

## Evidence

`scripts/inspect_filesystem_mutation_lane.py` exercises the Python core
`LocalFileManager` in a temporary workspace only. It proposes one artifact-file
patch, creates an exact `LocalApprovalAuthority` grant, applies the patch
atomically, creates a separate exact rollback approval, rolls back, and checks
that a duplicate apply is blocked by idempotency replay.

The inspection output is safe refs and booleans only. It does not print the
temporary path, raw file path, old content, new content, raw diff, shell command,
or environment details.

Verified posture:

- proposal status: `proposed`
- apply status: `applied`
- rollback status: `rolled_back`
- duplicate apply status: `blocked`
- workspace scope: `temporary_workspace_only`
- safe path class: `single_artifact_file_ref`
- raw content persisted: `false`
- raw path persisted: `false`
- Control Center apply route enabled: `false`
- backend apply route enabled: `false`
- shell/subprocess execution enabled: `false`
- broad filesystem authority enabled: `false`

## Boundary

This evidence verifies the Python core lane only. It does not add a
`/files/patch/apply` route, does not expose Control Center apply controls, does
not write repo files, does not permit home-directory writes, does not permit
delete/export, does not allow unreviewed generated changes, and does not grant
shell/subprocess authority.

The visible Files workbench remains proposal/review-only until a separate PR
scopes API/CLI/UI receipt parity for an apply route.
