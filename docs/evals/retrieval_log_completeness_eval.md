# Retrieval Log Completeness Eval

Status: Eval specification.
Version: v0.5.6.

## Purpose

Verify that grounded answers store query, methods, source IDs, ranking metadata, selected evidence, ignored sources, timestamps, and evidence manifest references.

## Pass criteria

```text
grounding policy is followed
truth source route is logged
Evidence Manifest is produced when required
unsupported/conflicted/stale claims are handled safely
no inaccessible source content leaks into output or logs
```

## Blocked modules until passing

```text
news providers
weather providers
email/message scanners
research summaries
proactive intelligence
high-stakes workflows
external source integrations
```
