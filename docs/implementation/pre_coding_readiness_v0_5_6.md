# Pre-Coding Readiness v0.5.6

Status: Ready for M0 after v0.5.6 consistency audit passes.

## Required before M0 coding

```text
v0.5.6 committed and tagged
working tree clean
consistency audit passes
remote sync verified, if possible
```

## M0 coding boundaries

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

## v0.5.4 primitives to wire in early

M0 may add schema validation for these docs/schemas. M0.5/M1 may implement Pydantic equivalents:

```text
result/error envelope
idempotency policy
actor context
temporal context
data classification
redaction policy
capability flags
service boundary interfaces
```

## Recommended first code order

```text
1. pyproject.toml and package skeleton
2. validation scripts
3. tests for validation scripts
4. FastAPI health/version route
5. CI workflow
6. Pydantic runtime hygiene models
7. contract tests for runtime hygiene models
8. Execution Contract and Context Pack models
```


## v0.5.6 context-survival primitives to wire in early

M0 may add schema validation for these docs/schemas. M2.5 may implement Pydantic equivalents:

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


## v0.5.6 pre-coding addition

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
