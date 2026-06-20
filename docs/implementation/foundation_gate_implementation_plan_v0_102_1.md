# Foundation Gate Implementation Plan v0.102.1

v0.102.1 keeps Foundation Gate coverage aligned with the Mattermost Agent Rooms
module baseline while preserving the existing contract-first and
disabled-by-default posture.

## Required Currentness Checks

- Active docs must preserve the current v0.102.1 / 0.102.1 baseline.
- Active docs must preserve checkpoint-m168 as the latest accepted repository
  checkpoint.
- Active docs must preserve checkpoint-m166 and checkpoint-m167 as accepted
  local model lane checkpoints.
- Product release-truth, public security posture, API docs, Control Center
  route/status docs, Mattermost route docs, release evidence docs, and version
  metadata must agree on the current baseline.
- Historical v0.102.0, v1.x, and v2.0.0 tags remain immutable audit records and
  must not be treated as current release authority.

## Required Commands

```bash
.venv/bin/python scripts/release/check_version_truth.py
.venv/bin/python scripts/verify_current_baseline.py
PYTHONPATH=src .venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
PYTHONPATH=src .venv/bin/python -m pytest
```

## Mattermost Bridge Rule

The Mattermost bridge is local self-hosted, disabled by default, safe-ref only,
and guarded by explicit local bridge configuration. It may store bindings,
idempotency refs, cooldown refs, redacted audit events, and receipts, but it
must not persist raw transcripts, tokens, attachments, cookies, credentials,
raw prompts, raw provider payloads, or private content.

## Denials

v0.102.1 does not allow Mattermost/OpenWebUI forks, production authority,
public distribution, public beta, arbitrary plugin execution, unrestricted
network/browser automation, credential or cookie handling, connector writes,
shell/subprocess execution, mobile control, memory writes, context injection,
model/provider output authority, raw transcript persistence, raw prompt export,
or raw provider payload export.
