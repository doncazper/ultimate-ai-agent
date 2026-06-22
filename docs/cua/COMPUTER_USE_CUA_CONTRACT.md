# Computer Use / CUA Contract Lane

Status: blocked/experimental contract lane

This lane prepares UAA for future Computer Use / CUA integration without
granting runtime authority today. CUA is an external capability adapter, not
core authority. Browser automation and native desktop CUA remain separate
lanes, and neither lane is enabled by this contract.

Machine-checkable release-surface source:

```text
docs/cua/cua_release_surface_manifest.json
```

Verifier:

```bash
.venv/bin/python scripts/verify_cua_contract_lane.py
```

## Current Scope

- Contract models only: capability contract, proposed-action envelope, and
  doctor/health result.
- Driver-independent capability negotiation only; no hardcoded driver or tool
  assumption.
- Structured safe refs only; no markdown/text parsing as authority.
- Element identifiers are ephemeral and bound to snapshot refs.
- Observe/capture planning comes before click/type planning.
- Driver lifecycle is explicit: absent, disabled/noop, degraded,
  untrusted, or future available-untrusted.
- Every future proposed action must flow through Action Envelope, exact
  approval, durable receipt, and Evidence Timeline before any execution lane is
  considered.

## Denied Today

The lane has no runtime driver, click/type route, screenshot capture, OS
accessibility access, subprocess CUA launch, browser automation under CUA,
connector write, provider call, or action execution. It does not inspect
permissions, apps, windows, displays, installed binaries, or processes.

CUA proposals must not include raw screenshots, raw OCR, raw accessibility-tree
text, raw local paths, usernames, hostnames, credentials, private UI content,
provider payloads, raw prompts, or raw responses.

CUA proposals must also reject password typing, credential entry, 2FA handling,
permission-dialog interaction, security settings changes, account deletion,
billing changes, connector writes, shell payload typing, prompt/screenshot
instruction authority, and automatic execution.

## Future Milestone Order

1. Contract-only release-surface visibility and verifiers.
2. Observe-only redacted capture proposal with no raw screenshot storage.
3. Manual handoff receipt for user-performed computer actions.
4. Exact-approved proposal-only actions with durable receipts and Evidence
   Timeline binding.
5. Narrow low-risk execution only after a future accepted milestone adds exact
   authority, rollback or safe-disable proof, and focused tests.

No release surface may imply shipped status, general availability, production
readiness, or enabled real computer control for this lane.
