# Pre-Coding Readiness v0.5.8

Status: M0 and M0.5 completed. Ready for M1 after v0.5.8 consistency audit passes.

## Required before M1 coding

```text
v0.5.8 committed and tagged
working tree clean
consistency audit passes
remote sync verified, if possible
```

## M0 coding boundaries (Completed)

Allowed:

```text
project scaffolding
validation scripts
minimal FastAPI app
pyproject.toml
.env.example
.gitignore
CI skeleton
basic tests
```

Not allowed:

```text
scanners
real provider adapters
credentialed integrations
email/message/calendar tools
companion proactivity
Skill Factory
self-improving code
model API calls
real Tool Broker actions
real Memory Service writes
external execution
real Agent SDK/A2A integrations
real local model runtime calls
```

## v0.5.4 primitives wired in early (Completed in M0.5)

Pydantic equivalents implemented:

```text
result/error envelope
idempotency policy
actor context
temporal context
data classification
redaction policy
capability flags
```

## Recommended first code order

```text
1. pyproject.toml and package skeleton (Done)
2. validation scripts (Done)
3. tests for validation scripts (Done)
4. FastAPI health/version route (Done)
5. CI workflow (Pending)
6. Pydantic runtime hygiene models (Done)
7. contract tests for runtime hygiene models (Done)
8. Execution Contract and Context Pack models (Next: M1)
```


## v0.5.8 context-survival primitives to wire in early

M0/M0.5 adds schema validation for these docs/schemas. M2.5 may implement Pydantic equivalents:

```text
Structured World State
Context Budget
Token accounting/calibration
Tool result retention/trimming
Prompt/tool bundle manifests
Prefix cache policy
Local runtime manifests/profiles/health
Local resource budget
Privacy routing policy
Agent SDK adapter manifest
A2A minimal Agent Card
```


## v0.5.8 pre-coding addition

The following must be treated as foundation contracts before truth-sensitive features are implemented:

```text
Truth Source Router
Grounding Policy
Evidence Manifest
ClaimEvidence
Source Conflict Report
Retrieval Log Entry
```

No factual answer should be considered verified unless it can produce source-backed evidence or explicitly state that evidence is unavailable.


## v0.5.8 pre-coding addition

M2 must preserve observability compatibility from the start:

```text
Event records include trace-compatible IDs.
Event names are stable and versioned.
OpenTelemetry GenAI mapping can be added without changing core ledger semantics.
W3C Trace Context propagation is supported across service boundaries.
CloudEvents/AsyncAPI remain future export/documentation targets, not M0/M1 blockers.
Telemetry export must use redacted payloads only.
```
