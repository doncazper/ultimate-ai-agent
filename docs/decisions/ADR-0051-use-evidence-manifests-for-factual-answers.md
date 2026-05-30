# ADR-0051: Use Evidence Manifests for Factual Answers

Status: Accepted.
Date: v0.5.6.

## Context

Answer-level citations are useful but not enough for verified task completion. The agent needs to know which claim is supported by which source, which claims are stale or unsupported, and where sources conflict.

## Decision

Use Evidence Manifests for factual, research, provider-backed, high-stakes, externally actionable, or verified outputs.

## Consequences

- QA can check claims individually.
- Receipts can link to evidence without exposing secrets.
- Unsupported claims can be removed or refused.
- Source conflicts can be surfaced explicitly.
