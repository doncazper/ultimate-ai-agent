# Shadow Replay Plan v0.5.0

## Purpose

Test foundation changes against prior run traces without mutating live files, memory, tools, or external systems.

## Replay modes

```text
dry_replay: run decision logic only
mock_tool_replay: substitute tool outputs from trace or fixtures
policy_replay: compare old vs new permission/model/tool decisions
regression_replay: compare final artifact summaries and event completeness
```

## First replay fixtures

```text
successful_memory_spec_generation
failed_tool_permission_request
approval_denied_external_action
memory_conflict_with_canonical_file
file_patch_hash_conflict
```

## Required output

```text
run_id
old_decisions
new_decisions
diffs
policy regressions
missing events
changed costs
changed model routes
pass/fail
```
