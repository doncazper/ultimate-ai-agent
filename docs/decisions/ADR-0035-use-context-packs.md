# ADR-0035: Use Context Packs as the Controlled Context Boundary

Status: Accepted in v0.4.6

## Context

The agent needs memory, files, specs, event history, permissions, model policy, web research, email/message content, and scanner signals. Dumping everything into prompts would be unsafe, expensive, noisy, and vulnerable to prompt injection.

## Decision

Use Context Packs to provide each model/subagent/tool with only the context needed for its task. Context Packs preserve source precedence, enforce privacy boundaries, mark untrusted content as evidence-only, and log exclusions/redactions/conflicts.

## Consequences

Positive:
- Reduces context pollution and sensitive-data leakage.
- Makes memory/file/web retrieval auditable.
- Gives verifier agents the right evidence without generator scratchpads.
- Supports contract tests and replay.

Tradeoffs:
- Requires a Context Pack Builder service and retrieval policy.
- Needs evals for relevance and leakage.
