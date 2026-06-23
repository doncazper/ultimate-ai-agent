# Golden Path Demo

Status: portfolio demo guide
Scope: local inspection path, not production readiness

This three-minute path shows how to evaluate the repo without granting new
runtime authority. It ties the Control Center shell back to the Python Agent
Core, OpenAPI/API manifest discipline, approval envelopes, redacted evidence,
and CLI parity.

## 1. Launch Or Inspect The Local Control Center

```bash
./scripts/dev/uaa launch-ui
```

Status: implemented local developer launcher.

This starts or reuses the local backend and Control Center shell. The shell is
an operator view over core/API truth; it does not mint authority.

Static visual-test snapshots are available in
[SCREENSHOTS.md](SCREENSHOTS.md).

## 2. Setup Assistant Preview

Open the Setup surface in the Control Center or review the static
[Setup Assistant snapshot](assets/control-center-setup.png).

What to look for:

- Dry-run setup state.
- Explicit approval requirements.
- Receipt and rollback refs.
- Installer, background-service, model-output, and broader runtime authority
  remaining blocked.

Status: partial/readiness surface. It previews local setup posture; it is not a
production installer claim.

## 3. Manifest And API Contract

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
```

Status: implemented verifier for the current OpenAPI boundary.

Also inspect:

- `/api/manifest` when the local backend is running.
- [docs/api/README.md](../api/README.md)
- [docs/api/openapi_contract.md](../api/openapi_contract.md)

What to look for:

- Route classifications.
- Stable operation IDs.
- Side-effect and authority posture.
- Public/protected route metadata.

## 4. Action Inbox Approval Envelope

Open `/actions` in the Control Center or review the
[Action Inbox snapshot](assets/control-center-actions.png).

What to look for:

- Action kind and exact scope.
- Approval requirement.
- Approval refs as identifiers, not authority by themselves.
- Idempotency refs.
- Receipt visibility and evidence refs.
- Blocked external authority refs.
- No generic `Execute` control.

Status: implemented for bounded Action decision and local-task lanes. Broader
execution, connector writes, shell/subprocess execution, provider/model
authority, and production authority remain blocked.

## 5. Evidence And Redaction

Open `/evidence` in the Control Center or review the
[Evidence snapshot](assets/control-center-evidence.png).

What to look for:

- Safe refs and redacted summaries.
- Receipt/audit/event posture.
- Explicit blocked states.
- No raw prompts, raw responses, raw provider payloads, raw local paths, raw
  logs, usernames, hostnames, credentials, or secret-like values.

Status: implemented bounded Evidence Timeline surface for safe-ref inspection.

## 6. CLI Parity

```bash
.venv/bin/python scripts/dev/uaa_founder_loop.py inspect
```

Status: implemented repo-local inspection path.

This prints safe refs for Today, Actions, receipts, and Evidence Timeline state
from the same Python core/storage truth used by the Control Center route
surfaces. The command output is safe-ref oriented and omits raw content and raw
paths.

## What This Demo Does Not Claim

- No production readiness.
- No public beta or public distribution.
- No broad autonomy.
- No unrestricted browsing, shell, network, or connector authority.
- No connector writes.
- No provider/model authority.
- No hidden context injection.
- No plugin runtime import or execution.
- No generic action execution.

Use [CURRENT_STATUS.md](CURRENT_STATUS.md) for the current implemented,
partial, planned, mock-only, blocked, and intentionally out-of-scope map.

