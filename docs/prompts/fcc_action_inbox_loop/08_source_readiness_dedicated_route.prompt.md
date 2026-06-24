# FCC-SOURCES-001 Dedicated Source Readiness Route

Role: You are a Principal Software Engineer implementing a narrow,
production-grade Founder Command Center read-only maturity upgrade.

Task: Promote source readiness from embedded Today/Briefing metadata toward a
dedicated backend-owned read-only unit.

Treat `AGENTS.md` as binding. Read it completely first.

This is a read-only/status maturity task. Do not add runtime authority.

Explicitly not in scope:
- generic execution
- connector writes
- email send/archive/delete/label/move
- calendar write
- account auth
- credential handling
- background polling or refresh
- raw email body ingestion
- raw calendar body ingestion
- raw contact details
- web fetching
- provider/model calls or authority
- memory writes
- context injection
- shell/subprocess execution
- browser automation
- plugin runtime import
- remote execution
- production/public release claims

Goal:
Add a dedicated, typed, read-only Source Readiness route and bind it through the
Control Center so Inbox/Sources can move toward rank 2 without pretending live
connectors exist.

Target route:

`GET /control-center/sources/readiness`

Route contract:
- route classification: read-only / non-mutating
- side-effect class: `local_dev_workspace_only` or the repo’s existing
  equivalent for local read models
- protected route posture consistent with adjacent Control Center read routes
- operation ID stable and unique
- typed response
- safe refs/redacted summaries only

Response should expose backend-owned source readiness for:
- inbox/email
- calendar
- tasks
- CRM-lite/manual notes
- repo
- local files

Allowed states:
- `ready`
- `blocked`
- `missing`
- `metadata_only`
- `unavailable`
- `not_configured`

Required safe fields:
- `schema_version`
- `source`
- `backend_owned`
- `generated_at` or safe equivalent if the repo already uses one
- `status`
- `source_readiness_items`
- `source_readiness_posture`
- `supported_statuses`
- `missing_contract_refs`
- `blocked_state_refs`
- `blocked_authority_refs`
- `next_safe_action`
- `route_refs`
- `evidence_refs`
- explicit booleans proving connector runtime, source refresh, notification
  delivery, account auth, raw source ingestion, and write authority are disabled

Implementation requirements:

1. Backend/core read model
- Reuse the existing Python Founder Loop source-readiness derivation where
  possible.
- Avoid duplicating policy values in React.
- If existing Today/Briefing code owns the readiness calculation, extract a
  Python helper/read model that all three surfaces can share.
- The dedicated route must return the same backend-owned readiness truth used
  by Today and Morning Briefing.
- Mock/degraded fallback must remain non-authoritative.

2. API contract alignment
- Add the route in the API layer using existing route patterns.
- Update OpenAPI expectations if route generation is contract-bound.
- Update `/api/manifest` expectations if Control Center routes are enumerated.
- Update route metadata/status manifest docs if applicable.
- Keep operation IDs stable and unique.
- Ensure the route is classified non-mutating and read-only.

3. Control Center UI binding
- Add frontend endpoint, client/type binding, and component rendering for the
  dedicated source readiness route.
- Prefer composing the existing Source Readiness card from API data rather than
  creating a second conflicting grammar.
- `/today` and `/briefing` may continue showing embedded readiness, but the UI
  should make clear when the dedicated route is available.
- `/inbox` or the relevant source surface should show the dedicated route’s
  readiness posture without adding connector controls.
- React may only render/filter the backend read model. It must not invent
  source state, connector readiness, authority, route safety, or rank maturity.

4. Operational maturity binding
- Update `docs/control_center/operational_maturity_manifest.json` only if the
  new route, UI/API binding, tests, and verifier support the claim.
- If Inbox/Sources moves to rank 2, add explicit `ui_status_binding` equivalent
  fields if required by the current verifier.
- If rank 2 is not fully justified, leave the rank unchanged and document the
  remaining blocker.
- The verifier must fail if a rank 2 source readiness claim lacks the dedicated
  route, frontend binding, route metadata, tests, or safe redaction posture.

5. Redaction and authority safety
- Do not expose raw prompts, raw responses, provider payloads, raw logs, raw
  local paths, usernames, hostnames, environment dumps, credentials, email
  bodies, calendar bodies, contact details, account identifiers, or
  secret-like values.
- Use safe refs, bounded summaries, and explicit blocked states.
- The response must make disabled connector/runtime authorities visible.

6. Tests and verifier hardening
Add or update focused tests proving:
- `GET /control-center/sources/readiness` returns typed backend-owned read-only
  source readiness.
- The route is non-mutating and route metadata/OpenAPI/API manifest agree.
- The response includes all supported states and disabled-authority booleans.
- The response is safe-ref-only/redacted.
- Today and Morning Briefing remain aligned with the dedicated read model.
- The Control Center renders the dedicated readiness route.
- Mock/degraded fallback cannot claim backend-owned source readiness.
- No connector write/send/archive/delete/calendar-write/account-auth/polling/
  raw-body controls appear.
- The maturity verifier catches unsupported rank 2 claims.

7. Documentation alignment
Update only the smallest relevant docs:
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- `docs/control_center/operational_maturity_manifest.json`
- `docs/kanban/founder_command_center_board.md`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md` only if language rules need
  tightening
- documentation index only if this route introduces a new canonical doc

Do not create a competing roadmap.

Suggested execution loop:
1. Read `AGENTS.md` and the relevant source-readiness/backend/frontend/tests.
2. Inspect `git status --short --branch`.
3. Implement backend read model and route.
4. Bind frontend endpoint/client/type/component.
5. Add focused tests and verifier rules.
6. Review the diff adversarially for authority expansion, stale product
   language, UI-only truth, route/API drift, and redaction leaks.
7. Run focused verification.
8. Patch any in-scope faults and rerun checks.

Required verification:
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_operational_maturity_manifest.py -q`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `make frontend-check`
- focused backend/frontend tests added for the source readiness route

If frontend visual baselines change, run:
- `cd apps/control-center && npm run visual:check --if-present`

Only update snapshots after confirming the UI changes are intentional.

Definition of done:
- Dedicated Source Readiness route exists and is backend-owned, read-only,
  typed, redacted, and route-metadata aligned.
- Control Center consumes/displays the dedicated route without minting truth.
- Today/Briefing embedded readiness remains consistent with the dedicated route.
- Mock/degraded fallback remains non-authoritative.
- Inbox/Sources maturity rank is changed only if manifest/verifier-backed.
- No connector runtime, connector writes, source polling, account auth, raw
  source ingestion, memory writes, context injection, shell, browser, provider,
  plugin, remote, or production authority is added.
- Final response lists files changed, maturity changes made or not made,
  behavior changed, behavior explicitly not added, tests/verifiers run with
  pass/fail, skipped/blocked checks, remaining risks, and git status.
