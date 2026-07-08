# UAA Runtime Evidence Audit Receipt Spine

Status: Phase 06 implemented read model. This is backend-owned, safe-ref-only
evidence lineage. It does not grant approval, execution, export, provider,
browser, shell, connector, background, public release, production, or broad
autonomy authority.

## Implemented Slice

UAA adds a Python Core read model at
`contract-ref:runtime-evidence-audit-spine:v1` and source
`python_core_runtime_evidence_audit_spine`.

The model is exposed through the existing
`GET /control-center/evidence/timeline` route as
`evidence_audit_receipt_spine` and through CLI:

```bash
python scripts/dev/uaa_founder_loop.py inspect-evidence-audit-spine
```

The read model groups existing Evidence Timeline refs into:

- plan changes
- approval waits
- action proposals
- execution receipts for exact accepted or receipt-only lanes
- memory proposals and review decisions
- blocked and no-go events
- recovery, idempotency, replay, rollback, and safe-disable posture

Each receipt envelope contains safe refs for receipt, run, action, approval,
side-effect class, authority decision, redacted input/output refs, artifact hash
ref, timestamp ref, verifier version ref, redaction status, evidence refs, audit
refs, idempotency refs, rollback refs, blocked refs, and missing receipt refs.

## Authority Boundary

This phase is read-only lineage over existing timeline, receipt, proof,
approval, audit, idempotency, rollback, and blocked refs. Control Center renders
the model but cannot mint authority.

Still blocked:

- provider/model calls
- provider SDK calls
- live web fetching
- browser automation
- connector writes or sends
- unrestricted shell/subprocess execution
- plugin runtime import
- remote execution
- external telemetry/export claims
- public release or production authority
- broad autonomy

## Safe Degradation

Missing receipts are explicit `missing-receipt:*` refs. The UI and CLI show the
unknown state instead of inventing success. Artifact hash refs and verifier refs
are local tamper-awareness metadata only, not production compliance claims.

## Verification

Focused coverage:

- `tests/test_runtime_evidence_audit.py`
- `scripts/verify_uaa_runtime_evidence_audit.py`
- Control Center Evidence route assertions in `apps/control-center/src/App.test.tsx`

The verifier checks the contract ref, source, group kinds, aggregate counts,
receipt envelope fields, missing receipt handling, denied authority flags,
documentation refs, and CLI parity.
