# v0.102.1 Master Plan

Release: v0.102.1 - Mattermost Agent Rooms module baseline.

The active product and package baseline is v0.102.1 / 0.102.1. This is an
incremental local-first module slice for Mattermost room integration while UAA
remains the policy, approval, receipt, audit, latency, rollback, and model
readiness authority layer.

## Goals

- Add first-class UAA Mattermost bridge contracts and `/integrations/mattermost`
  route metadata.
- Add predefined speak-only roles for planner, summarizer, critic,
  implementer, safety-reviewer, and facilitator.
- Add redacted local bridge storage for bindings, idempotency, receipts, audit
  events, and cooldown state without raw transcript persistence.
- Add an in-repo Mattermost plugin scaffold with disabled-by-default local
  configuration, channel allowlisting, bounded event forwarding, dedupe, role
  bot mapping, and safe error handling.
- Update OpenAPI, API manifest, route currentness docs, Foundation Gate route
  normalization, tests, and baseline metadata.

## Non-Goals

- No Mattermost fork and no OpenWebUI fork.
- No production authority, public beta, public distribution, hosted service, or
  external release claim.
- No automatic Mattermost bot lifecycle management in this slice.
- No arbitrary plugin execution, credential/cookie handling, unrestricted
  network or browser automation, connector writes, shell/subprocess execution,
  memory writes, context injection, raw transcript storage, raw prompt export,
  or model/provider authority.

## Verification

- `make test`
- `make ruff`
- `.venv/bin/python scripts/release/check_version_truth.py`
- `.venv/bin/python scripts/verify_current_baseline.py --skip-static-scans`
- `PYTHONPATH=src .venv/bin/python scripts/verify_documentation_integrity.py`
- `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
- `PYTHONPATH=src .venv/bin/python scripts/run_foundation_gate.py --command-mode report-only`
- `cd integrations/mattermost-plugin && go test ./...` when Go is installed
