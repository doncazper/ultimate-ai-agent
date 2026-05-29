# Observability Replay Eval

Status: v0.4.7 foundation eval.

## Purpose

Ensure foundational changes can be tested against historical runs without mutating production state.

## Eval cases

```text
Replay a completed spec-generation run.
Replay a failed tool-call run.
Replay an approval-denied run.
Replay a memory-conflict run.
Replay a scanner-alert decision as dry run.
```

## Expected result

The replay harness reconstructs run state, identifies decisions that would change under new code, and produces a diff without executing external tools.
