# 55 — Tool Result Retention and Context Trimming

Status: Active foundation contract in v0.5.5.

## Purpose

Tool results can be large, noisy, and expensive to keep in active model context. The system should preserve raw results outside the transcript and retain only compact references or summaries in live context.

## Trimming policy

Never trim:

```text
system/developer policy
current user instruction
active Execution Contract
active World State
active consent/approval constraints
active safety constraints
accepted user decisions
```

Trim last:

```text
recent user messages
high-value reasoning summaries
verified decisions
```

Trim first:

```text
large raw tool outputs
logs
base64 blobs
large tables
raw provider payloads
duplicate search results
stale intermediate observations
```

## Retention requirements

- Raw results must be stored as artifacts, file references, or Event Ledger payload references before being removed from live context.
- Context should contain compact result summaries, evidence references, hashes, file paths, or artifact IDs.
- The largest eligible context items should be trimmed first when nearing budget.
- User messages should not be trimmed by default because they carry intent and constraints.
- Every trim action must produce a `context_trim_event`.
