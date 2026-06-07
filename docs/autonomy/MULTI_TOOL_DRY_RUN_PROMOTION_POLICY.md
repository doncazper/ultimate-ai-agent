# Multi-Tool Dry-Run Promotion Policy

The M93 policy is deterministic, local-only, safe refs only, and review-only. It requires a dry-run plan, a real-run plan, matching plan hash refs, exact promotion approval, and dry-run and real-run equivalence.

Wildcard approval denied means broad refs, approval_test_ refs, and non-promotion approval refs cannot authorize promotion. Approval refs are identifiers only.

The policy denies real-run execution, tool execution, autonomous execution, session start, background worker, command execution, shell execution, subprocess execution, filesystem mutation, network access, browser click, browser form, plugin execution, remote execution, model call, memory write, context injection, backend route, Control Center control, dependency, and production authority.

Evaluator boundaries revalidate policy and request fields. M94 remains future.
