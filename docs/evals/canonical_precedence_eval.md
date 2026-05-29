# Canonical Precedence Eval

Status: v0.4.9 foundation eval.

## Purpose

Ensure canonical files outrank memory and conversation history except where the current user explicitly changes direction.

## Required checks

```text
Canonical > project memory.
Active spec > old conversation.
Current explicit user instruction can trigger canonical update workflow, but does not silently rewrite truth.
Memory source references point to canonical files after updates.
```
