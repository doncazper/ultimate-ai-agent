# UAA GoatCitadel Runtime Parity Final Hardening

Status: implemented as backend-owned inspection parity, not broad runtime
authority.

Phase 08 adds one final runtime loop read model that ties the Phase 01-07
surfaces together for operators:

- prepared turn;
- route-decision binding;
- durable run and approval wait;
- staged orchestration;
- role-based model/provider evidence;
- Action Inbox approval envelope;
- exact action receipt;
- local signed evidence;
- blocked, degraded, retry, and recovery posture.

## Implemented Surfaces

- Python Core read model:
  `build_runtime_parity_loop_read_model`.
- API:
  `GET /api/runtime/parity-loop`.
- CLI:
  `scripts/dev/uaa_runtime.py inspect-parity-loop`.
- Control Center:
  the Runtime Action Inbox bridge projects the parity loop API/CLI refs and
  stage refs into `/actions`.
- Verifier:
  `scripts/verify_uaa_goatcitadel_runtime_parity_final.py`.

## Authority Boundary

This read model performs no execution and grants no authority. It stores safe
refs, redacted summaries, counts, and blocked-authority refs only. Control
Center cannot mint authority from this read model. Control Center cannot mint
approval, execution, provider, browser, connector, shell, remote, background,
or production authority from this surface.

Still blocked:

- runtime model calls beyond separately accepted exact lanes;
- provider SDK calls;
- live web fetching;
- browser automation;
- connector writes;
- unrestricted shell or subprocess execution;
- plugin runtime import;
- remote execution;
- production authority;
- broad autonomy;
- raw prompt, response, provider payload, local path, log, credential, or
  secret-like persistence.

## Promotion Path

Future parity work should promote only exact lanes. Each new lane must prove
approval binding, idempotency, safe-disable or rollback posture, receipt refs,
proof/evidence refs, redaction, CLI/API/Core parity, route classification, and
focused verifier coverage before it can move beyond blocked/read-only posture.
