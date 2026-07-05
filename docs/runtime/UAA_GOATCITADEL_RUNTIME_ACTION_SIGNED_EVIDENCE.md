# UAA GoatCitadel Runtime Action Signed Evidence

Status: implemented for the exact focused pytest Action Inbox lane.

This phase borrows GoatCitadel's operator-visible execution spine without
copying GoatCitadel code or importing GoatCitadel packages. UAA keeps Python
Agent Core as the source of truth and exposes signed evidence as local,
safe-ref-only receipt metadata.

This does not copy GoatCitadel code. The signed evidence is local hash
verification, Control Center cannot mint authority, broad runtime authority
remains blocked, and no unrestricted shell is added.

- signed evidence is local hash verification
- broad runtime authority remains blocked

## What Is Implemented

- Exact focused pytest Action Inbox lane evidence through
  `RuntimeGateway`.
- `RuntimeActionSignedEvidenceEnvelope` with approval ref, exact scope ref,
  policy decision ref, route-decision binding ref, payload fingerprint ref,
  receipt ref, rollback ref, safe-disable ref, artifact hash refs, and evidence
  refs.
- Stable canonical JSON hash and local signed-envelope ref. The signed evidence
  is local hash verification, not public notarization or external trust.
- Offline verifier through `verify_runtime_action_signed_evidence`.
- API receipt detail includes `signed_evidence_available`,
  `signed_evidence_envelope`, and `signed_evidence_verification` when an action
  receipt exists.
- CLI parity:
  - `scripts/dev/uaa_runtime.py receipts evidence <receipt-ref>`
  - `scripts/dev/uaa_runtime.py receipts verify-evidence --input <json>`
- Control Center Action Inbox bridge includes `signed_evidence_refs`,
  `signed_evidence_cli_ref`, and `signed_evidence_verifier_cli_ref`.

## Still Blocked

- Broad runtime authority remains blocked.
- No unrestricted shell.
- No arbitrary command text.
- No browser automation.
- No connector writes.
- No plugin runtime import.
- No remote execution.
- No provider/model call authority from the evidence envelope.
- No production authority, public notarization, public release, or public beta
  claim.

## Redaction

The envelope stores no raw command output, no raw prompt or response, no raw
provider payload, no raw local path, no environment dump, no credential
material, and no raw logs. It stores safe refs, booleans, bounded status, hashes,
and verifier refs only.

## Promotion Path

Future lanes may add signed evidence for other exact approved actions only when
each lane proves approval binding, idempotency, replay conflict detection,
rollback or safe-disable posture, receipt refs, proof refs, redaction, CLI/API
parity, route classification, and focused verifier coverage.
