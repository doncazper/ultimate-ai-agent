# UAA Hermes Runtime LSP Diagnostics

Phase 34 adds backend-owned semantic diagnostic proof posture for the Hermes
Runtime Adoption program. It is evidence-contract only, not language server
launch, dependency install, shell execution, file access, provider call, or raw
diagnostic payload persistence authority.

## Full-Strength

UAA can attach semantic diagnostics to coding proof after changes. A mature lane
would let UAA supervise allowlisted language diagnostics, receipt the diagnostic
run, redact raw output, and link diagnostic evidence to Proof Detail for coding
tasks.

## Repo-Safe

The current implementation is read/evidence only:

- Python Agent Core owns `RuntimeLspDiagnosticsReadModel`.
- API route: `GET /api/runtime/lsp-diagnostics`.
- CLI inspection: `scripts/dev/uaa_runtime.py inspect-lsp-diagnostics`.
- AuthorityState binding: `lane-ref:runtime-lsp-diagnostics-evidence`
  evaluates as Full local workspace `workspace/read` authority through
  `GET /api/runtime/authority-state` and
  `repo-local-command:uaa-runtime-inspect-authority-state`.
- Control Center renders diagnostic refs, safe source scope refs, evidence refs,
  receipt-plan refs, proof refs, redaction posture, promotion requirements, and
  blocked authority refs, authority decision refs, blocked reason refs, and
  unsupported adapter refs.
- Mock fallback is visibly non-authoritative and keeps language-server launch,
  dependency install, shell execution, file access, provider calls, raw paths,
  and raw diagnostic payload persistence blocked.
- No LSP server, dependency install, shell command, file read/write, provider
  call, or raw diagnostic payload persistence is performed.

## Blocked / Needs Authority

These remain blocked:

- language server launch
- dependency installation
- shell execution
- file reads and writes
- provider/model calls
- Control Center minting authority
- raw local path persistence
- raw diagnostic payload or language-server log persistence

Known but unsupported adapter refs:

- `adapter-ref:lsp-server-launch:not-implemented`
- `adapter-ref:lsp-file-read:not-implemented`
- `adapter-ref:lsp-diagnostic-extraction:not-implemented`

## Exact Authority Path

Live diagnostics require all of the following before any real diagnostic lane
can run under an active AuthorityLease:

- allowlisted language server or argv-only diagnostic command
- cwd jail and workspace scope
- timeout and output bounds
- redaction contract
- diagnostic receipt
- proof link
- approval binding
- idempotency
- safe-disable posture
- CLI/API/Core parity
- focused tests and verifier coverage
- route side-effect classification
- Control Center labels that distinguish evidence placeholder, proof-ready,
  blocked, and executable states

Unknown authority remains denied. Known LSP diagnostic authority inside the
current catalog remains denied because the language-server launch, file-read,
diagnostic extraction, dependency install, timeout, redaction, and receipted
evidence adapters are not implemented or tested.

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_lsp_diagnostics.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_34.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
npm run test --prefix apps/control-center -- --run src/App.test.tsx src/routes.test.ts src/api/client.summaryEndpoints.test.ts
```

The verifier fails if the route is missing, classification drifts, CLI parity is
lost, or any language-server launch, dependency install, shell execution, file
read/write, provider call, raw path persistence, raw diagnostic payload
persistence, or Control Center authority flag is enabled.
