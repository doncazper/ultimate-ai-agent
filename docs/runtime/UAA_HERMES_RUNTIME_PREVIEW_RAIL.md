# UAA Hermes Runtime Preview Rail

Phase 35 adds backend-owned right preview rail posture for the Hermes Runtime
Adoption program. It is safe-ref and bounded-preview posture only, not browser
automation, raw sensitive file display, direct runtime payload rendering, file
access, shell execution, provider calls, or screenshot capture authority.

## Full-Strength

UAA previews files, diffs, artifacts, screenshots, run output, proof, and
delegated runtime events beside chat. A mature rail would let the operator
inspect classified sources, attach previews to tasks, receipt preview
artifacts, and link visual/proof evidence without losing redaction boundaries.

## Repo-Safe

The current implementation is read/safe-ref only:

- Python Agent Core owns `RuntimePreviewRailReadModel`.
- API route: `GET /api/runtime/preview-rail`.
- CLI inspection: `scripts/dev/uaa_runtime.py inspect-preview-rail`.
- AuthorityState binding:
  `lane-ref:runtime-preview-rail-safe-ref-read-model` evaluates as Read-only
  `workspace/read` authority through `GET /api/runtime/authority-state` and
  `repo-local-command:uaa-runtime-inspect-authority-state`.
- `scripts/dev/uaa_runtime.py inspect-preview-rail` returns the same mapping,
  decision, reason, and unsupported-adapter refs as the Python Core read model.
- Control Center renders preview slot refs, source classification refs,
  bounded preview refs, redaction policy refs, attach-plan refs, receipt-plan
  refs, proof refs, authority decision refs, blocked reason refs, promotion
  requirements, and blocked authority refs.
- Mock fallback is visibly non-authoritative and keeps browser automation, raw
  sensitive file display, direct runtime payload rendering, screenshot capture,
  file reads/writes, shell execution, provider calls, raw paths, raw file
  content, and raw runtime payload persistence blocked.
- No browser action, screenshot capture, file read/write, shell command,
  provider call, or raw runtime payload rendering is performed.

## Blocked / Needs Authority

These remain blocked:

- live browser automation
- raw sensitive file display
- direct runtime payload rendering
- screenshot capture
- file reads and writes
- shell execution
- provider/model calls
- Control Center minting authority
- raw local path persistence
- raw file content persistence
- raw runtime payload persistence

## Exact Authority Path

Safe-ref preview rail inspection is implemented as an authority-bound read
model. Rendering live data or raw/screenshot/browser previews still requires
all of the following before any real preview lane can run under an active
AuthorityLease:

- source classification
- redaction contract
- bounded preview limits
- operator attach plan
- receipt/proof link
- approval binding if a preview source would mutate or fetch
- idempotency where attachment is persisted
- safe-disable posture
- CLI/API/Core parity
- focused tests and verifier coverage
- route side-effect classification
- visual tests for desktop and mobile presentation

Unknown authority remains denied. The current allowed AuthorityState decision
applies only to safe refs, bounded preview plans, receipt-plan refs, and proof
refs. It does not allow file reads, raw file display, browser automation,
screenshot capture, shell execution, provider calls, direct runtime payload
rendering, or raw path/content persistence.

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_preview_rail.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_35.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
npm run test --prefix apps/control-center -- --run src/App.test.tsx src/routes.test.ts src/api/client.summaryEndpoints.test.ts
```

The verifier fails if the route is missing, classification drifts, CLI parity
is lost, or any browser automation, raw sensitive file display, direct runtime
payload rendering, screenshot capture, file access, shell execution, provider
call, raw path persistence, raw file-content persistence, raw runtime-payload
persistence, or Control Center authority flag is enabled.
