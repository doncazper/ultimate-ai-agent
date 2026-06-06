# v0.88.0 Master Plan

## Scope

M84 adds a sandboxed echo/no-op command contract only.

## Acceptance

- The command is in-process only.
- The command is deterministic and local-only.
- The command binds exactly to an M83 no-effect shell dry-run classifier
  decision.
- Receipt plans store safe summary only metadata.
- Evaluator boundaries revalidate request, M83 decision, result, and receipt
  fields.
- Static verification blocks shell/subprocess/process execution drift.
- OpenAPI path count remains stable.

## Non-Goals

M84 adds no shell string, raw command, raw output, command execution, subprocess
execution, shell execution, process spawn, filesystem mutation, network access,
tool execution, browser automation, plugin execution, remote execution, model
call, memory write, context injection, background worker, backend route, Control
Center control, dependency, M85 work, or production authority.

M85 remains future.
