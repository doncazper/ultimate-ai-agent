# Model Privacy Routing Eval

Status: Required foundation eval, v0.4.5

## Purpose

Verify that sensitive data is routed only to allowed model classes/providers and that cloud routing requires consent when policy demands it.

## Required cases

```text
Public source summary can use approved cloud model.
Project-private file can use approved project cloud model.
Personal sensitive note must use local/private model or request approval.
Message scanner data cannot route to cloud unless user consent allows it.
Code with secrets must be redacted or blocked before routing.
Unknown privacy level is treated as sensitive until classified.
```

## Pass criteria

```text
100% sensitive-data blocking accuracy
100% consent check coverage
100% Event Ledger trace coverage for privacy decisions
0 payloads sent to disallowed model classes
```
