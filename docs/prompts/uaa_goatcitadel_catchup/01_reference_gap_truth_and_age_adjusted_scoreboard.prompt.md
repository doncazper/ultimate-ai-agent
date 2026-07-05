# Phase 01: Reference Gap Truth And Age-Adjusted Scoreboard

Goal: establish a code-evidenced catch-up baseline before implementation. The
output must be a UAA-owned scorecard and backlog that distinguishes real code
from docs, mocks, screenshots, aspirations, and blocked authority.

This phase is inspection, documentation, and verifier work. It must not add
runtime authority.

## Required Work

1. Record current UAA branch, commit, package/version baseline, dirty files,
   primary runtime/language, main app surfaces, backend/core surfaces,
   CLI/script surfaces, and relevant tests/verifiers.
2. If the sibling GoatCitadel repo is available, record the same high-level
   facts read-only. Do not persist absolute local paths.
3. Build a UAA vs GoatCitadel catch-up matrix focused on agent-platform
   components:
   - reasoning and task understanding;
   - planning and orchestration;
   - learning and adaptation;
   - memory and context management;
   - communication and interaction;
   - action and tool calling;
   - autonomy and authority management;
   - code and implementation assistance;
   - research/web/external information handling;
   - model/provider management;
   - evidence, audit, and observability;
   - safety, security, and failure handling;
   - UX as an AI cockpit;
   - CLI/API parity;
   - extensibility and ecosystem;
   - productized agent loop.
4. Add an age-adjusted view that separates:
   - what UAA already does better because of stricter governance;
   - what GoatCitadel does better because of older or broader product surface;
   - what UAA can catch up on without broad authority;
   - what UAA should defer until exact authority lanes are accepted.
5. Convert the top catch-up gaps into a ranked implementation backlog with:
   - target status;
   - owner surface;
   - route/API/CLI/UI impact;
   - authority needed or blocked;
   - tests/verifiers required;
   - first safe PR lane.

## UAA Outputs

Create or update the smallest appropriate docs. Prefer one dedicated report
such as:

`docs/control_center/UAA_GOATCITADEL_CATCHUP_SCOREBOARD.md`

The report must include:

- branch and commit evidence;
- source files inspected;
- component scores or maturity labels;
- age-adjusted interpretation;
- ranked catch-up backlog;
- explicit "not copied from GoatCitadel" statement;
- explicit blocked authority list.

Add a verifier such as:

`scripts/verify_uaa_goatcitadel_catchup_scoreboard.py`

The verifier should fail if the report omits statuses, authority boundaries,
test references, or product-language limits.

## Acceptance Criteria

- Every major claim cites UAA files or marks the evidence unknown.
- GoatCitadel is used only as a reference comparator.
- The report distinguishes implemented, partial, planned, mock-only, blocked,
  deprecated, contradicted, and unknown states.
- No runtime model, web, connector, browser, shell, plugin, memory-write, or
  production authority is added.
- The backlog can drive Phases 02-09 without reopening broad generic audit.

## Verification

Run:

```bash
git diff --check
.venv/bin/python scripts/verify_uaa_goatcitadel_catchup_scoreboard.py
.venv/bin/python scripts/verify_documentation_integrity.py
```

